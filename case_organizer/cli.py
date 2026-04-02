from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer
import uvicorn

from case_organizer.config import Settings
from case_organizer.exporters import (
    export_ca199_toolbox_bundle_json,
    export_indicators_csv,
    export_medications_csv,
    export_patient_summary_json,
    export_standard_case_json,
    export_timeline_events_csv,
)
from case_organizer.extract import MinerURunner, read_local_file
from case_organizer.extract.archive_resolver import resolve_result_directory
from case_organizer.extract.document_normalizer import normalize_manifest
from case_organizer.models.document import DocumentEnvelope
from case_organizer.normalize.fact_extractor import extract_candidate_case
from case_organizer.normalize.template_mapper import to_printable_sections
from case_organizer.review.wizard_service import initialize_case_directory
from case_organizer.review.app import build_review_app
from case_organizer.review.storage import ReviewStorage
from case_organizer.scanner.file_index import FileIndex
from case_organizer.scanner.file_scanner import scan_supported_files

app = typer.Typer(help="Case Organizer CLI")

LOCAL_DIRECT_EXTENSIONS = {".csv", ".md", ".txt", ".xls", ".xlsx"}
MINERU_BACKED_EXTENSIONS = {".doc", ".docx", ".jpeg", ".jpg", ".pdf", ".png", ".webp"}


def _initialize_case_directory(case_dir: Path) -> dict[str, str]:
    return initialize_case_directory(case_dir)


def _resolve_scan_directories(path: str, workspace: str | None) -> tuple[Path, Path]:
    input_path = Path(path)
    if not input_path.exists():
        raise typer.BadParameter(f"source path does not exist: {input_path}")

    raw_dir = input_path / "raw"
    if raw_dir.is_dir():
        source_dir = raw_dir
        workspace_dir = Path(workspace) if workspace else input_path / "workspace"
        return source_dir, workspace_dir

    source_dir = input_path
    workspace_dir = Path(workspace) if workspace else Path("./workspace")
    return source_dir, workspace_dir


def _build_local_envelope(file_path: Path, file_id: str) -> DocumentEnvelope:
    local_result = read_local_file(file_path)
    return DocumentEnvelope(
        file_id=file_id,
        file_path=str(file_path),
        file_type=file_path.suffix.lower(),
        extract_status="resolved",
        ocr_used=False,
        text_content=local_result.text_content,
        structured_data={
            "reader": local_result.reader,
            "tables": local_result.tables,
            "source_path": local_result.source_path,
        },
        page_texts=[local_result.text_content] if local_result.text_content else [],
        tables=local_result.tables,
        attachments=[],
        source_meta={
            "reader": local_result.reader,
            "source_path": local_result.source_path,
        },
        source_manifest={
            "reader": local_result.reader,
            "source_path": local_result.source_path,
        },
    )


def _build_pipeline_manifest(
    source_dir: Path,
    workspace_dir: Path,
    mineru_enabled: bool,
    processed_files: list[Path],
    deferred_mineru_files: list[Path],
    mineru_processed_files: list[Path],
    failed_mineru_files: list[dict[str, str]],
    outputs: dict[str, str],
) -> dict[str, object]:
    return {
        "source_dir": str(source_dir),
        "workspace_dir": str(workspace_dir),
        "mineru_enabled": mineru_enabled,
        "processed_files": [str(path) for path in processed_files],
        "deferred_mineru_files": [str(path) for path in deferred_mineru_files],
        "mineru_processed_files": [str(path) for path in mineru_processed_files],
        "failed_mineru_files": failed_mineru_files,
        "outputs": outputs,
        "processed_count": len(processed_files),
        "deferred_mineru_count": len(deferred_mineru_files),
        "mineru_processed_count": len(mineru_processed_files),
        "failed_mineru_count": len(failed_mineru_files),
    }


def _build_mineru_envelope(
    file_path: Path,
    file_id: str,
    extract_root: Path,
) -> DocumentEnvelope:
    result_zip_path = extract_root / "result.zip"
    manifest = resolve_result_directory(
        source_file=str(file_path),
        result_zip_path=result_zip_path,
        extract_dir=extract_root,
    )
    manifest_path = extract_root / "extraction_manifest.json"
    manifest_path.write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return normalize_manifest(manifest, file_id=file_id, file_type=file_path.suffix.lower())


def _scan_pipeline(source_dir: Path, workspace_dir: Path) -> dict[str, object]:
    settings = Settings(workspace_dir=workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir = workspace_dir / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir = workspace_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    file_index = FileIndex(workspace_dir / "file_index.json")
    scanned_files = scan_supported_files(source_dir)
    document_envelopes: list[DocumentEnvelope] = []
    processed_files: list[Path] = []
    deferred_mineru_files: list[Path] = []
    mineru_processed_files: list[Path] = []
    failed_mineru_files: list[dict[str, str]] = []
    mineru_runner = MinerURunner(settings) if settings.mineru_api_token else None

    for file_path in scanned_files:
        track_result = file_index.track(file_path)
        if not track_result.should_process:
            continue

        processed_files.append(file_path)
        suffix = file_path.suffix.lower()

        if suffix in LOCAL_DIRECT_EXTENSIONS:
            document_envelopes.append(_build_local_envelope(file_path, track_result.file_id))
            continue

        if suffix in MINERU_BACKED_EXTENSIONS:
            if mineru_runner is None:
                deferred_mineru_files.append(file_path)
                continue

            try:
                target_dir = extracted_dir / track_result.file_id
                extract_root = asyncio.run(
                    mineru_runner.run_local_file_upload(file_path, target_dir)
                )
                if extract_root is None:
                    failed_mineru_files.append(
                        {"file_path": str(file_path), "reason": "no_extract_result"}
                    )
                    continue

                document_envelopes.append(
                    _build_mineru_envelope(file_path, track_result.file_id, extract_root)
                )
                mineru_processed_files.append(file_path)
            except Exception as exc:
                failed_mineru_files.append(
                    {"file_path": str(file_path), "reason": str(exc)}
                )
            continue

    candidate_case = extract_candidate_case(document_envelopes)
    candidate_payload = {
        "standard_case": candidate_case.model_dump(),
        "printable_sections": to_printable_sections(candidate_case),
        "source_documents": candidate_case.source_documents,
        "local_documents": [
            {
                "file_id": envelope.file_id,
                "file_path": envelope.file_path,
                "file_type": envelope.file_type,
                "reader": envelope.source_meta.get("reader"),
            }
            for envelope in document_envelopes
        ],
        "deferred_mineru_files": [str(path) for path in deferred_mineru_files],
        "mineru_processed_files": [str(path) for path in mineru_processed_files],
        "failed_mineru_files": failed_mineru_files,
    }

    review_storage = ReviewStorage(workspace_dir)
    review_storage.save_candidate_case(candidate_payload)

    outputs = {
        "candidate_case": str(review_storage.candidate_case_path),
        "standard_case": str(export_standard_case_json(candidate_case, normalized_dir)),
        "patient_summary": str(export_patient_summary_json(candidate_case, normalized_dir)),
        "ca199_bundle": str(export_ca199_toolbox_bundle_json(candidate_case, normalized_dir)),
        "indicators": str(export_indicators_csv(candidate_case, normalized_dir)),
        "medications": str(export_medications_csv(candidate_case, normalized_dir)),
        "timeline_events": str(export_timeline_events_csv(candidate_case, normalized_dir)),
    }

    manifest = _build_pipeline_manifest(
        source_dir=source_dir,
        workspace_dir=workspace_dir,
        mineru_enabled=bool(settings.mineru_api_token),
        processed_files=processed_files,
        deferred_mineru_files=deferred_mineru_files,
        mineru_processed_files=mineru_processed_files,
        failed_mineru_files=failed_mineru_files,
        outputs=outputs,
    )
    (workspace_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest


@app.command()
def init(path: str) -> None:
    """Initialize a patient case directory template."""
    created = _initialize_case_directory(Path(path))
    typer.echo(
        "initialized case directory: "
        f"raw={created['raw_dir']} "
        f"workspace={created['workspace_dir']} "
        f"exports={created['exports_dir']}"
    )


@app.command()
def scan(path: str, workspace: str | None = None) -> None:
    """Scan a patient case directory or raw document directory and export a normalized bundle."""
    source_dir, workspace_dir = _resolve_scan_directories(path, workspace)
    manifest = _scan_pipeline(source_dir, workspace_dir)
    typer.echo(
        "scan complete: "
        f"{manifest['processed_count']} processed, "
        f"{manifest['deferred_mineru_count']} deferred MinerU files"
    )


@app.command()
def review(path: str, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Open the local review app for a workspace."""
    workspace = Path(path)
    uvicorn.run(build_review_app(workspace), host=host, port=port)


@app.command()
def export(path: str) -> None:
    """Export normalized outputs for ca199_toolbox."""
    print(f"export {path}")


if __name__ == "__main__":
    app()
