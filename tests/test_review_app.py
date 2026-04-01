from __future__ import annotations

import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

from case_organizer.review.app import build_review_app
from case_organizer.review.storage import ReviewStorage


def _set_case_root(monkeypatch, tmp_path: Path) -> Path:
    case_root = tmp_path / "cases"
    monkeypatch.setenv("CASE_ORGANIZER_CASE_ROOT", str(case_root))
    return case_root


def test_review_storage_round_trip(tmp_path: Path) -> None:
    storage = ReviewStorage(tmp_path)
    payload = {"patient": {"name": "张三"}, "status": "draft"}

    saved_path = storage.save_candidate_case(payload)

    assert saved_path == tmp_path / "candidate_case.json"
    assert storage.load_candidate_case() == payload


def test_review_app_renders_wizard_shell(tmp_path: Path, monkeypatch) -> None:
    case_root = _set_case_root(monkeypatch, tmp_path)
    ReviewStorage(tmp_path / "workspace").save_candidate_case(
        {"diagnosis": {"primary_diagnosis": "胰腺导管腺癌"}}
    )

    app = build_review_app(tmp_path)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "病情资料整理向导" in response.text
    assert "创建病例" in response.text
    assert "放入资料" in response.text
    assert "data-step-panel=\"6\"" in response.text
    assert "wizard.js" in response.text
    assert "胰腺导管腺癌" in response.text
    assert str(case_root) in response.text


def test_review_app_returns_health_check(tmp_path: Path, monkeypatch) -> None:
    _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_wizard_init_endpoint_creates_case_directories(tmp_path: Path, monkeypatch) -> None:
    case_root = _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    response = client.post("/api/wizard/init", json={"case_name": "patient001"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_dir"] == str(case_root / "patient001")
    assert Path(payload["raw_dir"]).is_dir()
    assert Path(payload["workspace_dir"]).is_dir()
    assert Path(payload["exports_dir"]).is_dir()
    assert (case_root / "patient001" / "raw" / "03_影像报告").is_dir()
    assert (case_root / "patient001" / "exports" / "legacy").is_dir()


def test_wizard_inspect_endpoint_reports_counts(tmp_path: Path, monkeypatch) -> None:
    _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    case_dir = tmp_path / "patient001"
    ReviewStorage(tmp_path / "workspace").save_candidate_case({})
    (case_dir / "raw" / "03_影像报告").mkdir(parents=True, exist_ok=True)
    (case_dir / "raw" / "03_影像报告" / "ct1.pdf").write_text("demo", encoding="utf-8")
    (case_dir / "raw" / "05_检验检查" / "01_肿瘤标志物").mkdir(parents=True, exist_ok=True)
    (case_dir / "raw" / "05_检验检查" / "01_肿瘤标志物" / "ca19_9.csv").write_text(
        "demo", encoding="utf-8"
    )

    response = client.get("/api/wizard/inspect", params={"case_dir": str(case_dir)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_files"] == 2
    assert payload["category_counts"]["03_影像报告"] == 1
    assert payload["category_counts"]["05_检验检查"] == 1


def test_wizard_upload_endpoint_writes_file_into_category(tmp_path: Path, monkeypatch) -> None:
    case_root = _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    init_response = client.post("/api/wizard/init", json={"case_name": "patient001"})
    case_dir = init_response.json()["case_dir"]
    content_base64 = base64.b64encode(b"binary-data").decode("ascii")

    response = client.post(
        "/api/wizard/upload",
        json={
            "case_dir": case_dir,
            "category_key": "03_影像报告",
            "filename": "ct.pdf",
            "content_base64": content_base64,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["saved_path"].endswith("/03_影像报告/ct.pdf")
    assert (case_root / "patient001" / "raw" / "03_影像报告" / "ct.pdf").read_bytes() == b"binary-data"


def test_wizard_upload_endpoint_rejects_file_over_10mb(tmp_path: Path, monkeypatch) -> None:
    _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    init_response = client.post("/api/wizard/init", json={"case_name": "patient001"})
    case_dir = init_response.json()["case_dir"]
    content_base64 = base64.b64encode(b"a" * (10 * 1024 * 1024 + 1)).decode("ascii")

    response = client.post(
        "/api/wizard/upload",
        json={
            "case_dir": case_dir,
            "category_key": "03_影像报告",
            "filename": "too-big.pdf",
            "content_base64": content_base64,
        },
    )

    assert response.status_code == 400
    assert "10MB" in response.json()["detail"]


def test_wizard_scan_endpoint_bridges_to_pipeline(tmp_path: Path, monkeypatch) -> None:
    _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    init_response = client.post("/api/wizard/init", json={"case_name": "patient001"})
    case_dir = Path(init_response.json()["case_dir"])
    (case_dir / "raw" / "03_影像报告" / "ct.pdf").write_text("demo", encoding="utf-8")

    def fake_scan_pipeline(source_dir: Path, workspace_dir: Path) -> dict[str, object]:
        workspace_dir.mkdir(parents=True, exist_ok=True)
        candidate_path = workspace_dir / "candidate_case.json"
        candidate_path.write_text(
            json.dumps({"diagnosis": {"primary_diagnosis": "胰腺导管腺癌"}}, ensure_ascii=False),
            encoding="utf-8",
        )
        return {
            "source_dir": str(source_dir),
            "workspace_dir": str(workspace_dir),
            "mineru_enabled": False,
            "processed_files": [str(source_dir / "ct.pdf")],
            "deferred_mineru_files": [],
            "mineru_processed_files": [],
            "failed_mineru_files": [],
            "outputs": {
                "candidate_case": str(candidate_path),
                "standard_case": str(workspace_dir / "normalized" / "standard_case.json"),
                "patient_summary": str(workspace_dir / "normalized" / "patient_summary.json"),
                "indicators": str(workspace_dir / "normalized" / "indicators.csv"),
                "medications": str(workspace_dir / "normalized" / "medications.csv"),
                "timeline_events": str(workspace_dir / "normalized" / "timeline_events.csv"),
            },
            "processed_count": 1,
            "deferred_mineru_count": 0,
            "mineru_processed_count": 0,
            "failed_mineru_count": 0,
        }

    monkeypatch.setattr("case_organizer.cli._scan_pipeline", fake_scan_pipeline)

    response = client.post("/api/wizard/scan", json={"case_dir": case_dir.as_posix()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["manifest"]["processed_count"] == 1
    assert payload["candidate_case"]["diagnosis"]["primary_diagnosis"] == "胰腺导管腺癌"


def test_wizard_export_summary_endpoint_reports_export_groups(tmp_path: Path, monkeypatch) -> None:
    _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    init_response = client.post("/api/wizard/init", json={"case_name": "patient001"})
    case_dir = init_response.json()["case_dir"]

    response = client.get("/api/wizard/export-summary", params={"case_dir": case_dir})

    assert response.status_code == 200
    payload = response.json()
    assert "normalized" in payload["exports"]
    assert "legacy" in payload["exports"]
    assert "printable" in payload["exports"]
    assert "summaries" in payload["exports"]


def test_wizard_delete_and_reassign_endpoints_manage_uploaded_file(tmp_path: Path, monkeypatch) -> None:
    case_root = _set_case_root(monkeypatch, tmp_path)
    app = build_review_app(tmp_path)
    client = TestClient(app)

    init_response = client.post("/api/wizard/init", json={"case_name": "patient001"})
    case_dir = init_response.json()["case_dir"]
    content_base64 = base64.b64encode(b"binary-data").decode("ascii")
    client.post(
        "/api/wizard/upload",
        json={
            "case_dir": case_dir,
            "category_key": "03_影像报告",
            "filename": "ct.pdf",
            "content_base64": content_base64,
        },
    )

    move_response = client.post(
        "/api/wizard/reassign",
        json={
            "case_dir": case_dir,
            "relative_path": "raw/03_影像报告/ct.pdf",
            "category_key": "06_处方与用药",
        },
    )
    assert move_response.status_code == 200
    assert (case_root / "patient001" / "raw" / "06_处方与用药" / "ct.pdf").exists()

    delete_response = client.post(
        "/api/wizard/delete",
        json={
            "case_dir": case_dir,
            "relative_path": "raw/06_处方与用药/ct.pdf",
        },
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
    assert not (case_root / "patient001" / "raw" / "06_处方与用药" / "ct.pdf").exists()


def test_wizard_js_contains_step_progression_hooks() -> None:
    wizard_js = Path(
        "/Users/qinxiaoqiang/Downloads/ca199_toolbox/case-organizer/"
        "case_organizer/review/static/wizard.js"
    ).read_text(encoding="utf-8")

    assert "goToStep" in wizard_js
    assert "createCase" in wizard_js
    assert "refreshInspect" in wizard_js
    assert "runScan" in wizard_js
    assert "loadExportSummary" in wizard_js
    assert "deleteFile" in wizard_js
    assert "reassignFile" in wizard_js
