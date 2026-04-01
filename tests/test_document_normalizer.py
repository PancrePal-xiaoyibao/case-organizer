from pathlib import Path

from case_organizer.extract.archive_resolver import resolve_result_directory
from case_organizer.extract.document_normalizer import normalize_manifest


def test_normalize_manifest_loads_text_json_and_assets(tmp_path: Path):
    extract_dir = tmp_path / "case"
    result_dir = extract_dir / "result"
    images_dir = result_dir / "images"
    images_dir.mkdir(parents=True)

    (result_dir / "full.md").write_text("# 病程概述\n患者治疗记录", encoding="utf-8")
    (result_dir / "content_list_v2.json").write_text(
        '{"tables":[{"name":"markers","rows":[{"name":"CA199","value":"120.5"}]}],"page_texts":["page one"]}',
        encoding="utf-8",
    )
    (result_dir / "layout.json").write_text('{"layout": true}', encoding="utf-8")
    (result_dir / "sample_origin.pdf").write_bytes(b"pdf")
    (images_dir / "preview.jpg").write_bytes(b"jpg")

    manifest = resolve_result_directory(
        source_file="source.pdf",
        result_zip_path=tmp_path / "result.zip",
        extract_dir=extract_dir,
    )
    envelope = normalize_manifest(manifest, file_id="file-001", file_type=".pdf")

    assert envelope.file_id == "file-001"
    assert envelope.file_path == "source.pdf"
    assert envelope.file_type == ".pdf"
    assert envelope.primary_text_path.endswith("result/full.md")
    assert envelope.text_content.startswith("# 病程概述")
    assert envelope.structured_data["tables"][0]["name"] == "markers"
    assert envelope.tables[0]["rows"][0]["name"] == "CA199"
    assert envelope.page_texts == ["page one"]
    assert envelope.attachments == [str(result_dir / "images" / "preview.jpg")]
    assert envelope.source_meta["resolver_version"] == "v1"
    assert envelope.source_meta["detected_files"][0] == "result/content_list_v2.json"


def test_normalize_manifest_handles_missing_primary_text(tmp_path: Path):
    extract_dir = tmp_path / "case"
    extract_dir.mkdir()

    manifest = resolve_result_directory(
        source_file="source.pdf",
        result_zip_path=tmp_path / "result.zip",
        extract_dir=extract_dir,
    )
    envelope = normalize_manifest(manifest, file_id="file-002", file_type=".pdf")

    assert envelope.text_content == ""
    assert envelope.structured_data == {}
    assert envelope.tables == []
    assert envelope.page_texts == []
