from pathlib import Path

from case_organizer.scanner.file_index import FileIndex


def test_track_marks_new_file_for_processing(tmp_path: Path):
    source = tmp_path / "doc.md"
    source.write_text("hello", encoding="utf-8")

    index = FileIndex(tmp_path / "manifest.json")

    result = index.track(source)

    assert result.should_process is True
    assert result.file_id


def test_track_skips_unchanged_file(tmp_path: Path):
    source = tmp_path / "doc.md"
    source.write_text("hello", encoding="utf-8")

    index = FileIndex(tmp_path / "manifest.json")

    first = index.track(source)
    second = index.track(source)

    assert first.should_process is True
    assert second.should_process is False

