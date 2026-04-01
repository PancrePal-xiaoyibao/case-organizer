from __future__ import annotations

from pathlib import Path

from case_organizer.review.case_layout import EXPORT_GROUPS, RAW_CATEGORY_GROUPS
from case_organizer.review.wizard_service import WizardService, get_default_case_root


def test_raw_category_groups_include_required_patient_categories() -> None:
    keys = [item["key"] for item in RAW_CATEGORY_GROUPS]

    assert keys == [
        "01_基本资料",
        "02_诊断报告书",
        "03_影像报告",
        "04_病理与基因",
        "05_检验检查",
        "06_处方与用药",
        "07_个人病情记录",
        "08_手术与住院资料",
        "99_待分类",
    ]

    fifth = RAW_CATEGORY_GROUPS[4]
    assert fifth["children"] == [
        "01_肿瘤标志物",
        "02_血常规",
        "03_肝肾功能",
        "04_凝血",
        "05_炎症指标",
        "06_体液检查_尿便常规",
        "07_其他检验",
    ]


def test_export_groups_are_legacy_compatible_and_ordered() -> None:
    assert EXPORT_GROUPS == ["normalized", "legacy", "printable", "summaries"]


def test_get_default_case_root_honors_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CASE_ORGANIZER_CASE_ROOT", str(tmp_path / "cases"))
    assert get_default_case_root() == tmp_path / "cases"


def test_initialize_case_creates_required_directories(tmp_path) -> None:
    service = WizardService()
    case_dir = tmp_path / "patient001"

    summary = service.initialize_case(case_dir)

    assert summary["case_dir"] == str(case_dir)
    assert (case_dir / "raw" / "01_基本资料").is_dir()
    assert (case_dir / "raw" / "05_检验检查" / "01_肿瘤标志物").is_dir()
    assert (case_dir / "raw" / "08_手术与住院资料").is_dir()
    assert (case_dir / "workspace").is_dir()
    assert (case_dir / "exports" / "normalized").is_dir()
    assert (case_dir / "exports" / "legacy").is_dir()
    assert (case_dir / "exports" / "printable").is_dir()
    assert (case_dir / "exports" / "summaries").is_dir()


def test_inspect_case_reports_file_counts(tmp_path) -> None:
    service = WizardService()
    case_dir = tmp_path / "patient001"
    service.initialize_case(case_dir)

    (case_dir / "raw" / "03_影像报告" / "ct1.pdf").write_text("demo", encoding="utf-8")
    (case_dir / "raw" / "05_检验检查" / "01_肿瘤标志物" / "ca19_9.csv").write_text(
        "demo", encoding="utf-8"
    )
    (case_dir / "raw" / "07_个人病情记录" / "note.md").write_text("demo", encoding="utf-8")

    summary = service.inspect_case(case_dir)

    assert summary["total_files"] == 3
    assert summary["category_counts"]["03_影像报告"] == 1
    assert summary["category_counts"]["05_检验检查"] == 1
    assert summary["category_counts"]["07_个人病情记录"] == 1
    assert len(summary["files"]) == 3


def test_save_upload_lists_move_and_delete_file(tmp_path) -> None:
    service = WizardService()
    case_dir = tmp_path / "patient001"
    service.initialize_case(case_dir)

    saved = service.save_upload(case_dir, "03_影像报告", "ct.pdf", b"demo")
    assert saved.exists()

    files = service.list_uploaded_files(case_dir)
    assert files[0]["relative_path"] == "raw/03_影像报告/ct.pdf"

    moved = service.move_file(case_dir, "raw/03_影像报告/ct.pdf", "06_处方与用药")
    assert moved.exists()
    assert moved.parent.name == "06_处方与用药"

    deleted = service.delete_file(case_dir, "raw/06_处方与用药/ct.pdf")
    assert deleted is True
    assert not moved.exists()
