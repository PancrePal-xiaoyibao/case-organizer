"""Map standard case data to printable case template sections."""

from __future__ import annotations

from case_organizer.models.case_data import StandardCase


PRINT_TEMPLATE_SECTIONS = [
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


def to_printable_sections(case: StandardCase) -> list[dict[str, object]]:
    """Convert a case into template-friendly sections."""
    return [
        {"title": "患者基本信息", "content": case.patient_profile.model_dump()},
        {"title": "核心诊断", "content": case.diagnosis.model_dump()},
        {"title": "基因检测", "content": [item.model_dump() for item in case.genomics]},
        {"title": "病理 / 免疫组化", "content": case.pathology.model_dump()},
        {"title": "既往治疗史", "content": [item.model_dump() for item in case.treatments]},
        {"title": "最近肿标", "content": [item.model_dump() for item in case.tumor_markers]},
        {"title": "近期影像资料", "content": [item.model_dump() for item in case.imaging_studies]},
        {"title": "患者现状", "content": case.current_status.model_dump()},
        {"title": "问诊需求 / 诉求", "content": [item.model_dump() for item in case.consult_questions]},
        {"title": "备注", "content": case.source_documents},
    ]

