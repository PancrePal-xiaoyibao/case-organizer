"""Persistent incremental file index."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrackResult:
    file_id: str
    should_process: bool


class FileIndex:
    """Track file hashes and mtimes to detect new or changed files."""

    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if not self.index_path.exists():
            return {"files": {}}

        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"files": {}}

    @staticmethod
    def _fingerprint(path: Path) -> dict:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"sha256": digest, "mtime": path.stat().st_mtime}

    def track(self, path: Path) -> TrackResult:
        """Persist the file fingerprint and return whether it should be processed."""
        key = str(path.resolve())
        current = self._fingerprint(path)
        previous = self._data["files"].get(key)
        should_process = previous != current

        self._data["files"][key] = current
        self.save()
        return TrackResult(file_id=current["sha256"], should_process=should_process)

    def save(self) -> None:
        self.index_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

