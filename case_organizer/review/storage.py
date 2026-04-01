"""Storage helpers for the local review app."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReviewStorage:
    """Read and write the candidate case payload for review."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir

    @property
    def candidate_case_path(self) -> Path:
        return self.workspace_dir / "candidate_case.json"

    def load_candidate_case(self) -> dict[str, Any]:
        if not self.candidate_case_path.exists():
            return {}
        try:
            return json.loads(self.candidate_case_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save_candidate_case(self, payload: dict[str, Any]) -> Path:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.candidate_case_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.candidate_case_path
