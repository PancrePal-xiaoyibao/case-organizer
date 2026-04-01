"""FastAPI app for the patient-facing review and wizard flow."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .wizard_service import MAX_UPLOAD_SIZE_BYTES, WizardService, get_default_case_root
from .storage import ReviewStorage
from .case_layout import EXPORT_GROUPS, RAW_CATEGORY_GROUPS


def _resolve_case_root(base_dir: Path) -> Path:
    if base_dir.name == "workspace":
        return base_dir.parent
    return base_dir


def _resolve_workspace_dir(base_dir: Path) -> Path:
    if base_dir.name == "workspace":
        return base_dir
    return base_dir / "workspace"


def build_review_app(workspace_dir: Path) -> FastAPI:
    workspace_dir = _resolve_workspace_dir(workspace_dir)
    current_case_root = _resolve_case_root(workspace_dir)
    case_root = get_default_case_root()
    storage = ReviewStorage(workspace_dir)
    wizard_service = WizardService()
    module_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=str(module_dir / "templates"))
    app = FastAPI(title="Case Organizer Review")
    app.mount("/static", StaticFiles(directory=str(module_dir / "static")), name="static")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    def _render_wizard(request: Request) -> HTMLResponse:
        candidate = storage.load_candidate_case()
        return templates.TemplateResponse(
            request,
            "wizard.html",
            {
                "title": "病情资料整理向导",
                "workspace_dir": str(workspace_dir),
                "case_root_dir": str(case_root),
                "current_case_root_dir": str(current_case_root),
                "candidate": candidate,
                "candidate_json": json.dumps(candidate, ensure_ascii=False, indent=2),
                "raw_categories": RAW_CATEGORY_GROUPS,
                "export_groups": EXPORT_GROUPS,
                "max_upload_size_mb": MAX_UPLOAD_SIZE_BYTES // (1024 * 1024),
            },
        )

    @app.get("/", response_class=HTMLResponse)
    async def wizard_page(request: Request) -> HTMLResponse:
        return _render_wizard(request)

    @app.get("/wizard", response_class=HTMLResponse)
    async def wizard_page_alias(request: Request) -> HTMLResponse:
        return _render_wizard(request)

    @app.get("/legacy", response_class=HTMLResponse)
    async def legacy_index(request: Request) -> HTMLResponse:
        candidate = storage.load_candidate_case()
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "title": "候选病情整理",
                "workspace_dir": str(workspace_dir),
                "case_root_dir": str(current_case_root),
                "candidate": candidate,
                "candidate_json": json.dumps(candidate, ensure_ascii=False, indent=2),
            },
        )

    @app.post("/api/wizard/init")
    async def wizard_init(payload: dict[str, str]) -> dict[str, str]:
        case_name = (payload.get("case_name") or "").strip()
        if not case_name:
            raise HTTPException(status_code=400, detail="case_name is required")
        case_dir = case_root / Path(case_name).name
        return wizard_service.initialize_case(case_dir)

    @app.get("/api/wizard/inspect")
    async def wizard_inspect(case_dir: str) -> dict[str, object]:
        return wizard_service.inspect_case(Path(case_dir))

    @app.get("/api/wizard/candidate")
    async def wizard_candidate() -> dict[str, object]:
        return {"candidate": storage.load_candidate_case()}

    @app.post("/api/wizard/upload")
    async def wizard_upload(payload: dict[str, str]) -> dict[str, str]:
        case_dir = (payload.get("case_dir") or "").strip()
        category_key = (payload.get("category_key") or "").strip()
        filename = (payload.get("filename") or "").strip()
        content_base64 = (payload.get("content_base64") or "").strip()

        if not case_dir:
            raise HTTPException(status_code=400, detail="case_dir is required")
        if not category_key:
            raise HTTPException(status_code=400, detail="category_key is required")
        if not filename:
            raise HTTPException(status_code=400, detail="filename is required")
        if not content_base64:
            raise HTTPException(status_code=400, detail="content_base64 is required")

        try:
            content = base64.b64decode(content_base64, validate=True)
        except Exception as exc:  # pragma: no cover - defensive decode guard
            raise HTTPException(status_code=400, detail="content_base64 is invalid") from exc

        try:
            saved_path = wizard_service.save_upload(
                Path(case_dir), category_key, filename, content
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"saved_path": str(saved_path)}

    @app.post("/api/wizard/delete")
    async def wizard_delete(payload: dict[str, str]) -> dict[str, object]:
        case_dir = (payload.get("case_dir") or "").strip()
        relative_path = (payload.get("relative_path") or "").strip()
        if not case_dir:
            raise HTTPException(status_code=400, detail="case_dir is required")
        if not relative_path:
            raise HTTPException(status_code=400, detail="relative_path is required")
        try:
            deleted = wizard_service.delete_file(Path(case_dir), relative_path)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"deleted": deleted}

    @app.post("/api/wizard/reassign")
    async def wizard_reassign(payload: dict[str, str]) -> dict[str, str]:
        case_dir = (payload.get("case_dir") or "").strip()
        relative_path = (payload.get("relative_path") or "").strip()
        category_key = (payload.get("category_key") or "").strip()
        if not case_dir:
            raise HTTPException(status_code=400, detail="case_dir is required")
        if not relative_path:
            raise HTTPException(status_code=400, detail="relative_path is required")
        if not category_key:
            raise HTTPException(status_code=400, detail="category_key is required")
        try:
            moved = wizard_service.move_file(Path(case_dir), relative_path, category_key)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"saved_path": str(moved)}

    @app.post("/api/wizard/scan")
    async def wizard_scan(payload: dict[str, str]) -> dict[str, object]:
        case_dir = (payload.get("case_dir") or "").strip()
        if not case_dir:
            raise HTTPException(status_code=400, detail="case_dir is required")
        return wizard_service.run_scan(Path(case_dir))

    @app.get("/api/wizard/export-summary")
    async def wizard_export_summary(case_dir: str) -> dict[str, object]:
        if not case_dir.strip():
            raise HTTPException(status_code=400, detail="case_dir is required")
        return wizard_service.export_summary(Path(case_dir))

    return app
