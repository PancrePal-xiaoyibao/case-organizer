from case_organizer.models.document import DocumentEnvelope
from case_organizer.normalize.fact_extractor import extract_candidate_case, to_printable_sections_from_envelopes


def test_extract_candidate_case_from_markdown_text():
    envelope = DocumentEnvelope(
        file_id="1",
        file_path="病例.md",
        file_type=".md",
        extract_status="resolved",
        ocr_used=False,
        text_content=(
            "病名\n胰腺导管腺癌pT3N0M0\n"
            "2025-05-20至今：北京协和医院使用全量nalirifox方案进行术后辅助化疗9次。"
        ),
        tables=[],
        attachments=[],
        source_meta={},
    )

    candidate = extract_candidate_case([envelope])

    assert candidate.diagnosis.primary_diagnosis == "胰腺导管腺癌pT3N0M0"
    assert candidate.treatments[0].regimen_name.lower() == "nalirifox"
    assert candidate.source_documents[0]["file_path"] == "病例.md"


def test_to_printable_sections_follow_template_order():
    envelope = DocumentEnvelope(
        file_id="1",
        file_path="病例.md",
        file_type=".md",
        extract_status="resolved",
        ocr_used=False,
        text_content="病名\n胰腺导管腺癌pT3N0M0",
        tables=[],
        attachments=[],
        source_meta={},
    )

    sections = to_printable_sections_from_envelopes([envelope])

    assert [section["title"] for section in sections] == [
        "患者基本信息",
        "核心诊断",
        "基因检测",
        "病理 / 免疫组化",
        "既往治疗史",
        "最近肿标",
        "近期影像资料",
        "患者现状",
        "问诊需求 / 诉求",
        "备注",
    ]

