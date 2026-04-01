from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from case_organizer import cli
from case_organizer.cli import app


def test_scan_pipeline_exports_normalized_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MINERU_API_TOKEN", raising=False)
    monkeypatch.delenv("MINERU_API_KEY", raising=False)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "case.md").write_text(
        "病名：胰腺导管腺癌pT3N0M0\n"
        "2025-05-20至今：北京协和医院使用全量nalirifox方案进行术后辅助化疗9次。\n",
        encoding="utf-8",
    )
    workspace_dir = tmp_path / "workspace"

    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(source_dir), "--workspace", str(workspace_dir)])

    assert result.exit_code == 0, result.stdout
    assert (workspace_dir / "manifest.json").exists()
    assert (workspace_dir / "candidate_case.json").exists()
    assert (workspace_dir / "normalized" / "standard_case.json").exists()
    assert (workspace_dir / "normalized" / "patient_summary.json").exists()
    assert (workspace_dir / "normalized" / "indicators.csv").exists()
    assert (workspace_dir / "normalized" / "medications.csv").exists()
    assert (workspace_dir / "normalized" / "timeline_events.csv").exists()

    manifest = json.loads((workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["processed_count"] == 1
    assert manifest["deferred_mineru_count"] == 0
    assert manifest["mineru_enabled"] is False

    candidate = json.loads((workspace_dir / "candidate_case.json").read_text(encoding="utf-8"))
    assert candidate["standard_case"]["diagnosis"]["primary_diagnosis"] == "胰腺导管腺癌pT3N0M0"
    assert candidate["printable_sections"][1]["title"] == "核心诊断"


@pytest.mark.usefixtures("monkeypatch")
def test_scan_pipeline_processes_mineru_backed_file_when_token_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "report.pdf").write_bytes(b"%PDF-1.4")
    workspace_dir = tmp_path / "workspace"

    async def fake_run_local_file_upload(self, file_path: Path, output_dir: Path, model_version: str = "vlm") -> Path:
        result_dir = output_dir / "result"
        result_dir.mkdir(parents=True)
        (result_dir / "full.md").write_text(
            "病名：胰腺导管腺癌pT3N0M0\n2025-05-20至今：北京协和医院使用全量nalirifox方案进行术后辅助化疗9次。\n",
            encoding="utf-8",
        )
        (result_dir / "content_list_v2.json").write_text(
            '{"page_texts":["page one"],"tables":[]}',
            encoding="utf-8",
        )
        (output_dir / "result.zip").write_bytes(b"zip")
        return output_dir

    monkeypatch.setenv("MINERU_API_TOKEN", "demo-token")
    monkeypatch.setattr(cli.MinerURunner, "run_local_file_upload", fake_run_local_file_upload)

    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(source_dir), "--workspace", str(workspace_dir)])

    assert result.exit_code == 0, result.stdout

    manifest = json.loads((workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["mineru_enabled"] is True
    assert manifest["mineru_processed_count"] == 1
    assert manifest["deferred_mineru_count"] == 0
    assert manifest["failed_mineru_count"] == 0

    extraction_manifests = list((workspace_dir / "extracted").rglob("extraction_manifest.json"))
    assert len(extraction_manifests) == 1

    candidate = json.loads((workspace_dir / "candidate_case.json").read_text(encoding="utf-8"))
    assert candidate["standard_case"]["diagnosis"]["primary_diagnosis"] == "胰腺导管腺癌pT3N0M0"
