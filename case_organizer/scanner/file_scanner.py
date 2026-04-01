"""Recursive scanner for supported patient documents."""

from __future__ import annotations

from pathlib import Path

from .file_types import SUPPORTED_EXTENSIONS


def scan_supported_files(root: Path) -> list[Path]:
    """Return supported files under *root* in deterministic order."""
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda path: str(path).lower())

