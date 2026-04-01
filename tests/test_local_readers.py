from pathlib import Path

from case_organizer.extract.local_readers import (
    read_local_csv,
    read_local_file,
    read_local_text,
)


def test_read_local_text_returns_raw_markdown(tmp_path: Path):
    path = tmp_path / "note.md"
    path.write_text("# 标题\n正文", encoding="utf-8")

    result = read_local_text(path)

    assert result.reader == "local_text"
    assert result.text_content == "# 标题\n正文"
    assert result.source_path == str(path)


def test_read_local_csv_returns_rows_and_text(tmp_path: Path):
    path = tmp_path / "markers.csv"
    path.write_text("name,value\nCA199,120.5\nCEA,45.2\n", encoding="utf-8")

    result = read_local_csv(path)

    assert result.reader == "local_csv"
    assert result.tables[0]["columns"] == ["name", "value"]
    assert result.tables[0]["rows"][0]["name"] == "CA199"
    assert "CA199, 120.5" in result.text_content


def test_read_local_file_dispatches_by_suffix(tmp_path: Path):
    path = tmp_path / "plain.txt"
    path.write_text("hello", encoding="utf-8")

    result = read_local_file(path)

    assert result.reader == "local_text"
    assert result.text_content == "hello"
