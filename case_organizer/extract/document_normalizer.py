"""Normalize MinerU manifests into reviewable case documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from case_organizer.models.document import DocumentEnvelope, ExtractionManifest


def _load_json_payload(path: str | None) -> dict[str, Any]:
    if not path:
        return {}

    file_path = Path(path)
    if not file_path.exists():
        return {}

    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    return {"items": payload}


def _extract_tables(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tables = payload.get("tables", [])
    return tables if isinstance(tables, list) else []


def _extract_page_texts(payload: dict[str, Any]) -> list[str]:
    page_texts = payload.get("page_texts", [])
    if isinstance(page_texts, list):
        return [str(item) for item in page_texts]
    return []


def normalize_manifest(manifest: ExtractionManifest, file_id: str, file_type: str) -> DocumentEnvelope:
    """Load the primary MinerU text/JSON pair into a normalized envelope."""

    text_content = ""
    if manifest.primary_text_path:
        text_path = Path(manifest.primary_text_path)
        if text_path.exists():
            text_content = text_path.read_text(encoding="utf-8")

    structured_data = _load_json_payload(manifest.primary_structured_path)
    tables = _extract_tables(structured_data)
    page_texts = _extract_page_texts(structured_data)

    return DocumentEnvelope(
        file_id=file_id,
        file_path=manifest.source_file,
        file_type=file_type,
        extract_status=manifest.status,
        ocr_used=True,
        result_zip_path=manifest.result_zip_path,
        extract_dir=manifest.extract_dir,
        primary_text_path=manifest.primary_text_path,
        primary_structured_path=manifest.primary_structured_path,
        layout_path=manifest.layout_path,
        origin_pdf_path=manifest.origin_pdf_path,
        text_content=text_content,
        structured_data=structured_data,
        page_texts=page_texts,
        tables=tables,
        attachments=list(manifest.asset_paths),
        source_meta={
            "detected_files": list(manifest.detected_files),
            "resolver_version": manifest.resolver_version,
        },
        source_manifest=manifest.model_dump(),
    )
