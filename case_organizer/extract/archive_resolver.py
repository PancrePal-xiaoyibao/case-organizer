"""Resolve MinerU result archives into a manifest."""

from __future__ import annotations

import uuid
from pathlib import Path

from case_organizer.models.document import ExtractionManifest


def _relative_files(extract_dir: Path) -> list[Path]:
    return sorted(
        (path.relative_to(extract_dir) for path in extract_dir.rglob("*") if path.is_file()),
        key=lambda item: (len(item.parts), item.as_posix().lower()),
    )


def _pick_first(candidates: list[Path]) -> str | None:
    if not candidates:
        return None
    return candidates[0].as_posix()


def _match_files(files: list[Path], predicate) -> list[Path]:
    return [path for path in files if predicate(path)]


def resolve_result_directory(
    source_file: str,
    result_zip_path: Path,
    extract_dir: Path,
    resolver_version: str = "v1",
) -> ExtractionManifest:
    """Inspect an extracted MinerU archive and pick explicit primary files."""

    detected_files = _relative_files(extract_dir)

    markdown_candidates = _match_files(
        detected_files,
        lambda path: path.name == "full.md" or path.suffix.lower() == ".md",
    )
    structured_candidates = _match_files(
        detected_files,
        lambda path: path.name == "content_list_v2.json"
        or path.name.endswith("_content_list.json")
        or path.name == "layout.json"
        or path.name.endswith("_model.json"),
    )
    layout_candidates = _match_files(detected_files, lambda path: path.name == "layout.json")
    origin_pdf_candidates = _match_files(
        detected_files,
        lambda path: path.name.endswith("_origin.pdf") or path.name == "origin.pdf",
    )
    asset_paths = [
        path.as_posix()
        for path in detected_files
        if "images" in path.parts
    ]

    primary_text_path = _pick_first(markdown_candidates)
    primary_structured_path = _pick_first(structured_candidates)
    layout_path = _pick_first(layout_candidates)
    origin_pdf_path = _pick_first(origin_pdf_candidates)

    status = "resolved" if primary_text_path or primary_structured_path else "partial"

    return ExtractionManifest(
        job_id=str(uuid.uuid4()),
        source_file=source_file,
        result_zip_path=str(result_zip_path),
        extract_dir=str(extract_dir),
        primary_text_path=str(extract_dir / primary_text_path) if primary_text_path else None,
        primary_structured_path=str(extract_dir / primary_structured_path) if primary_structured_path else None,
        layout_path=str(extract_dir / layout_path) if layout_path else None,
        origin_pdf_path=str(extract_dir / origin_pdf_path) if origin_pdf_path else None,
        asset_paths=[str(extract_dir / rel_path) for rel_path in asset_paths],
        detected_files=[path.as_posix() for path in detected_files],
        status=status,
        resolver_version=resolver_version,
    )
