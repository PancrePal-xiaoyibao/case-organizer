from pathlib import Path

from case_organizer.exporters.csv_exporter import (
    export_indicators_csv,
    export_medications_csv,
    export_timeline_events_csv,
)
from case_organizer.exporters.json_exporter import export_ca199_toolbox_bundle_json
from case_organizer.models.case_data import (
    ClinicalEvent,
    StandardCase,
    TreatmentPhase,
    TumorMarker,
)


def test_export_indicators_csv_writes_expected_header_and_rows(tmp_path: Path):
    case = StandardCase(
        tumor_markers=[
            TumorMarker(
                test_date="2025-04-01",
                indicator_name="CA199",
                indicator_value=24.5,
                unit="U/mL",
                reference_low=0,
                reference_high=37,
                source_file="marker.pdf",
                source_page=1,
                confidence=0.95,
            )
        ]
    )

    path = export_indicators_csv(case, tmp_path)

    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0] == (
        "test_date,indicator_name,indicator_value,unit,reference_low,"
        "reference_high,source_file,source_page,confidence"
    )
    assert "2025-04-01,CA199,24.5,U/mL,0.0,37.0,marker.pdf,1,0.95" in text


def test_export_medications_csv_maps_treatments_to_medication_rows(tmp_path: Path):
    case = StandardCase(
        treatments=[
            TreatmentPhase(
                phase_id="phase-1",
                regimen_name="FOLFIRINOX",
                start_date="2025-01-01",
                end_date="2025-03-01",
                source_files=["treatment.docx"],
            )
        ]
    )

    path = export_medications_csv(case, tmp_path)

    text = path.read_text(encoding="utf-8")
    assert "start_date,end_date,drug_name,tag,source_file,confidence" in text
    assert "2025-01-01,2025-03-01,FOLFIRINOX,FOLFIRINOX,treatment.docx,1.0" in text


def test_export_timeline_events_csv_uses_related_sources(tmp_path: Path):
    case = StandardCase(
        clinical_events=[
            ClinicalEvent(
                event_date="2025-02-01",
                event_type="检查",
                title="CT复查",
                description="结果稳定",
                doctor_note="继续随访",
                patient_note="无明显不适",
                next_step="三个月后复查",
                related_sources=["ct.pdf", "note.md"],
            )
        ]
    )

    path = export_timeline_events_csv(case, tmp_path)

    text = path.read_text(encoding="utf-8")
    assert "event_date,event_type,title,description,doctor_note,patient_note,next_step,source_file" in text
    assert "2025-02-01,检查,CT复查,结果稳定,继续随访,无明显不适,三个月后复查,ct.pdf;note.md" in text


def test_export_ca199_toolbox_bundle_json_contains_normalized_sections(tmp_path: Path):
    case = StandardCase(
        tumor_markers=[
            TumorMarker(
                test_date="2025-04-01",
                indicator_name="CA199",
                indicator_value=24.5,
                unit="U/mL",
                source_file="marker.pdf",
            )
        ],
        treatments=[
            TreatmentPhase(
                phase_id="phase-1",
                regimen_name="FOLFIRINOX",
                start_date="2025-01-01",
                end_date="2025-03-01",
                source_files=["treatment.docx"],
            )
        ],
        clinical_events=[
            ClinicalEvent(
                event_date="2025-02-01",
                event_type="检查",
                title="CT复查",
                related_sources=["ct.pdf"],
            )
        ],
    )

    path = export_ca199_toolbox_bundle_json(case, tmp_path)
    text = path.read_text(encoding="utf-8")

    assert '"source_mode": "normalized"' in text
    assert '"indicator_name": "CA199"' in text
    assert '"drug_name": "FOLFIRINOX"' in text
    assert '"title": "CT复查"' in text
