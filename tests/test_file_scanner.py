from pathlib import Path

from case_organizer.scanner.file_scanner import scan_supported_files
from case_organizer.scanner.file_types import SUPPORTED_EXTENSIONS


def test_supported_extensions_cover_required_inputs():
    expected = {
        ".csv",
        ".doc",
        ".docx",
        ".jpeg",
        ".jpg",
        ".md",
        ".pdf",
        ".png",
        ".txt",
        ".webp",
        ".xls",
        ".xlsx",
    }

    assert SUPPORTED_EXTENSIONS == expected


def test_scan_supported_files_filters_and_sorts_recursively(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    (nested / "a.pdf").write_text("a", encoding="utf-8")
    (nested / "ignore.exe").write_text("x", encoding="utf-8")
    (tmp_path / "c.txt").write_text("c", encoding="utf-8")

    files = scan_supported_files(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in files] == [
        "b.md",
        "c.txt",
        "nested/a.pdf",
    ]

