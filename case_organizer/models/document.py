"""Shared document models for extracted case data."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractionManifest(BaseModel):
    """Resolved MinerU output paths for a single source document."""

    job_id: str
    source_file: str
    result_zip_path: str
    extract_dir: str
    primary_text_path: str | None = None
    primary_structured_path: str | None = None
    layout_path: str | None = None
    origin_pdf_path: str | None = None
    asset_paths: list[str] = Field(default_factory=list)
    detected_files: list[str] = Field(default_factory=list)
    status: str = "resolved"
    resolver_version: str = "v1"


class DocumentEnvelope(BaseModel):
    """Normalized document payload used by downstream case extraction."""

    file_id: str
    file_path: str
    file_type: str
    extract_status: str
    ocr_used: bool
    result_zip_path: str | None = None
    extract_dir: str | None = None
    primary_text_path: str | None = None
    primary_structured_path: str | None = None
    layout_path: str | None = None
    origin_pdf_path: str | None = None
    text_content: str = ""
    structured_data: dict[str, Any] = Field(default_factory=dict)
    page_texts: list[str] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    source_meta: dict[str, Any] = Field(default_factory=dict)
    source_manifest: dict[str, Any] | None = None
