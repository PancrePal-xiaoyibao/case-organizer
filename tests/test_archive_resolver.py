from pathlib import Path

from case_organizer.extract.archive_resolver import resolve_result_directory


def test_resolve_result_directory_prefers_primary_mineru_outputs(tmp_path: Path):
    extract_dir = tmp_path / "case"
    result_dir = extract_dir / "result"
    images_dir = result_dir / "images"
    images_dir.mkdir(parents=True)

    (result_dir / "full.md").write_text("# 病程概述\n正文", encoding="utf-8")
    (result_dir / "content_list_v2.json").write_text('{"tables":[{"name":"markers"}]}', encoding="utf-8")
    (result_dir / "layout.json").write_text('{"layout": true}', encoding="utf-8")
    (result_dir / "sample_origin.pdf").write_bytes(b"pdf")
    (images_dir / "preview.jpg").write_bytes(b"jpg")
    (result_dir / "notes.txt").write_text("extra", encoding="utf-8")

    manifest = resolve_result_directory(
        source_file="source.pdf",
        result_zip_path=tmp_path / "result.zip",
        extract_dir=extract_dir,
    )

    assert manifest.status == "resolved"
    assert manifest.primary_text_path.endswith("result/full.md")
    assert manifest.primary_structured_path.endswith("result/content_list_v2.json")
    assert manifest.layout_path.endswith("result/layout.json")
    assert manifest.origin_pdf_path.endswith("result/sample_origin.pdf")
    assert manifest.asset_paths == [str(result_dir / "images" / "preview.jpg")]
    assert "result/full.md" in manifest.detected_files
    assert "result/content_list_v2.json" in manifest.detected_files


def test_resolve_result_directory_marks_partial_when_primary_files_missing(tmp_path: Path):
    extract_dir = tmp_path / "empty_case"
    extract_dir.mkdir()
    (extract_dir / "other.json").write_text("{}", encoding="utf-8")

    manifest = resolve_result_directory(
        source_file="source.pdf",
        result_zip_path=tmp_path / "result.zip",
        extract_dir=extract_dir,
    )

    assert manifest.status == "partial"
    assert manifest.primary_text_path is None
    assert manifest.primary_structured_path is None
