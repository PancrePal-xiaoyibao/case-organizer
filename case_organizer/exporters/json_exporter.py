"""JSON exporters for standardized case-organizer outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from case_organizer.models.case_data import StandardCase


def export_patient_summary_json(case: StandardCase, output_dir: Path) -> Path:
    """Export the concise patient summary used by case readers."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "patient_summary.json"
    payload: dict[str, Any] = {
        "patient_name": case.patient_profile.name,
        "primary_diagnosis": case.diagnosis.primary_diagnosis,
        "key_metrics": [marker.indicator_name for marker in case.tumor_markers],
        "current_phase": case.diagnosis.current_phase,
        "last_updated_at": None,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_standard_case_json(case: StandardCase, output_dir: Path) -> Path:
    """Export the full structured case as JSON for review/debugging."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "standard_case.json"
    path.write_text(case.model_dump_json(indent=2), encoding="utf-8")
    return path
