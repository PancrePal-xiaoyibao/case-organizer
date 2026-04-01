"""CSV exporters for the ca199_toolbox file-level contract."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

from case_organizer.models.case_data import StandardCase


INDICATOR_FIELDNAMES = [
    "test_date",
    "indicator_name",
    "indicator_value",
    "unit",
    "reference_low",
    "reference_high",
    "source_file",
    "source_page",
    "confidence",
]

MEDICATION_FIELDNAMES = [
    "start_date",
    "end_date",
    "drug_name",
    "tag",
    "source_file",
    "confidence",
]

TIMELINE_FIELDNAMES = [
    "event_date",
    "event_type",
    "title",
    "description",
    "doctor_note",
    "patient_note",
    "next_step",
    "source_file",
]


def _coerce_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _coerce_scalar(row.get(field)) for field in fieldnames})
    return path


def export_indicators_csv(case: StandardCase, output_dir: Path) -> Path:
    """Export tumor markers as `indicators.csv`."""
    rows = [marker.model_dump() for marker in case.tumor_markers]
    return _write_csv(output_dir / "indicators.csv", INDICATOR_FIELDNAMES, rows)


def export_medications_csv(case: StandardCase, output_dir: Path) -> Path:
    """Export treatment phases as `medications.csv`."""
    rows: list[dict[str, Any]] = []
    for phase in case.treatments:
        rows.append(
            {
                "start_date": phase.start_date,
                "end_date": phase.end_date,
                "drug_name": phase.regimen_name,
                "tag": phase.regimen_name,
                "source_file": ";".join(phase.source_files),
                "confidence": 1.0,
            }
        )
    return _write_csv(output_dir / "medications.csv", MEDICATION_FIELDNAMES, rows)


def export_timeline_events_csv(case: StandardCase, output_dir: Path) -> Path:
    """Export clinical events as `timeline_events.csv`."""
    rows: list[dict[str, Any]] = []
    for event in case.clinical_events:
        payload = event.model_dump()
        rows.append(
            {
                "event_date": payload.get("event_date"),
                "event_type": payload.get("event_type"),
                "title": payload.get("title"),
                "description": payload.get("description"),
                "doctor_note": payload.get("doctor_note"),
                "patient_note": payload.get("patient_note"),
                "next_step": payload.get("next_step"),
                "source_file": ";".join(payload.get("related_sources", [])),
            }
        )
    return _write_csv(output_dir / "timeline_events.csv", TIMELINE_FIELDNAMES, rows)
