"""Extract candidate case facts from normalized documents."""

from __future__ import annotations

import re
from collections.abc import Iterable

from case_organizer.models.case_data import (
    ClinicalEvent,
    Diagnosis,
    StandardCase,
    TreatmentPhase,
)
from case_organizer.models.document import DocumentEnvelope
from .template_mapper import to_printable_sections


_DIAGNOSIS_PATTERNS = [
    re.compile(r"病名[：:\s]*([^\n]+)"),
    re.compile(r"病理诊断[：:\s]*([^\n]+)"),
]

_TREATMENT_PATTERNS = [
    re.compile(r"(nalirifox)", re.IGNORECASE),
    re.compile(r"(FOLFIRINOX)", re.IGNORECASE),
    re.compile(r"(AG方案)", re.IGNORECASE),
    re.compile(r"(白蛋白紫杉醇)", re.IGNORECASE),
    re.compile(r"(替吉奥)", re.IGNORECASE),
]


def _join_text(envelopes: Iterable[DocumentEnvelope]) -> str:
    parts: list[str] = []
    for envelope in envelopes:
        if envelope.text_content.strip():
            parts.append(envelope.text_content)
    return "\n".join(parts)


def _extract_first_match(patterns: list[re.Pattern[str]], text: str) -> str | None:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            return value or None
    return None


def _extract_treatment_name(text: str) -> str | None:
    for pattern in _TREATMENT_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def extract_candidate_case(envelopes: Iterable[DocumentEnvelope]) -> StandardCase:
    """Build a conservative candidate case from one or more extracted documents."""
    envelope_list = list(envelopes)
    text = _join_text(envelope_list)
    case = StandardCase()

    diagnosis = _extract_first_match(_DIAGNOSIS_PATTERNS, text)
    if diagnosis:
        case.diagnosis = Diagnosis(primary_diagnosis=diagnosis)

    treatment_name = _extract_treatment_name(text)
    if treatment_name:
        case.treatments.append(
            TreatmentPhase(
                phase_id="phase-1",
                regimen_name=treatment_name,
                source_files=[envelope.file_path for envelope in envelope_list],
            )
        )

    event_matches = []
    for envelope in envelope_list:
        if envelope.source_manifest:
            source_name = envelope.file_path
            event_matches.append(
                ClinicalEvent(
                    event_date=None,
                    event_type="文档整理",
                    title=source_name,
                    description=envelope.text_content[:500] if envelope.text_content else "",
                    related_sources=[source_name],
                )
            )
    case.clinical_events.extend(event_matches)
    case.source_documents = [
        {
            "file_path": envelope.file_path,
            "file_id": envelope.file_id,
            "file_type": envelope.file_type,
        }
        for envelope in envelope_list
    ]
    return case


def to_printable_sections_from_envelopes(envelopes: Iterable[DocumentEnvelope]) -> list[dict[str, object]]:
    """Convenience helper for turning extracted documents into printable sections."""
    return to_printable_sections(extract_candidate_case(envelopes))

