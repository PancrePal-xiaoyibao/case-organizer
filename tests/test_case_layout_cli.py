from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from case_organizer.cli import app


def test_init_creates_case_directory_template(tmp_path: Path) -> None:
    case_dir = tmp_path / "patient001"

    runner = CliRunner()
    result = runner.invoke(app, ["init", str(case_dir)])

    assert result.exit_code == 0, result.stdout
    assert (case_dir / "raw" / "01_基本资料").is_dir()
    assert (case_dir / "raw" / "05_检验检查" / "01_肿瘤标志物").is_dir()
    assert (case_dir / "raw" / "08_手术与住院资料").is_dir()
    assert (case_dir / "workspace").is_dir()
    assert (case_dir / "exports" / "normalized").is_dir()
    assert (case_dir / "exports" / "printable").is_dir()
    assert (case_dir / "exports" / "summaries").is_dir()


def test_scan_uses_case_directory_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("MINERU_API_TOKEN", raising=False)
    monkeypatch.delenv("MINERU_API_KEY", raising=False)

    case_dir = tmp_path / "patient001"
    raw_dir = case_dir / "raw"
    (raw_dir / "07_个人病情记录").mkdir(parents=True)
    (raw_dir / "07_个人病情记录" / "case.md").write_text(
        "病名：胰腺导管腺癌pT3N0M0\n"
        "2025-05-20至今：北京协和医院使用全量nalirifox方案进行术后辅助化疗9次。\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["scan", str(case_dir)])

    assert result.exit_code == 0, result.stdout
    assert (case_dir / "workspace" / "manifest.json").exists()
    assert (case_dir / "workspace" / "candidate_case.json").exists()
    assert (case_dir / "workspace" / "normalized" / "patient_summary.json").exists()

