"""Wizard-specific helpers for the patient-facing web flow."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .case_layout import RAW_CATEGORY_GROUPS

EXPORT_GROUPS = ["normalized", "legacy", "printable", "summaries"]
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


def _category_paths() -> list[Path]:
    paths: list[Path] = []
    for category in RAW_CATEGORY_GROUPS:
        key = category["key"]
        if key == "05_检验检查":
            paths.extend(
                [
                    Path("raw") / key / child
                    for child in category.get("children", [])
                ]
            )
            continue
        paths.append(Path("raw") / key)
    return paths


def initialize_case_directory(case_dir: Path) -> dict[str, str]:
    raw_dir = case_dir / "raw"
    workspace_dir = case_dir / "workspace"
    exports_dir = case_dir / "exports"

    for rel_path in _category_paths():
        (case_dir / rel_path).mkdir(parents=True, exist_ok=True)
    for export_subdir in EXPORT_GROUPS:
        (exports_dir / export_subdir).mkdir(parents=True, exist_ok=True)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    return {
        "case_dir": str(case_dir),
        "raw_dir": str(raw_dir),
        "workspace_dir": str(workspace_dir),
        "exports_dir": str(exports_dir),
    }


def get_default_case_root() -> Path:
    configured = os.getenv("CASE_ORGANIZER_CASE_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser()
    return (Path.cwd() / "output").resolve()


class WizardService:
    def initialize_case(self, case_dir: Path) -> dict[str, str]:
        return initialize_case_directory(case_dir)

    def _category_exists(self, category_key: str) -> bool:
        return any(category["key"] == category_key for category in RAW_CATEGORY_GROUPS)

    def _category_target_dir(self, case_dir: Path, category_key: str) -> Path:
        if category_key == "05_检验检查":
            raise ValueError("category_key must target a specific child category")

        if "/" in category_key:
            base, child = category_key.split("/", 1)
            if base != "05_检验检查":
                raise ValueError(f"unknown category: {category_key}")
            return case_dir / "raw" / base / child

        return case_dir / "raw" / category_key

    def save_upload(
        self,
        case_dir: Path,
        category_key: str,
        filename: str,
        content: bytes,
    ) -> Path:
        if not (self._category_exists(category_key) or category_key.startswith("05_检验检查/")):
            raise ValueError(f"unknown category: {category_key}")
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError("file exceeds 10MB limit")

        safe_name = Path(filename).name
        target = self._category_target_dir(case_dir, category_key) / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return target

    def delete_file(self, case_dir: Path, relative_path: str) -> bool:
        target = (case_dir / relative_path).resolve()
        raw_root = (case_dir / "raw").resolve()
        if raw_root not in target.parents:
            raise ValueError("file must be inside case raw directory")
        if not target.exists() or not target.is_file():
            return False
        target.unlink()
        return True

    def move_file(self, case_dir: Path, relative_path: str, category_key: str) -> Path:
        source = (case_dir / relative_path).resolve()
        raw_root = (case_dir / "raw").resolve()
        if raw_root not in source.parents:
            raise ValueError("file must be inside case raw directory")
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(relative_path)

        target_dir = self._category_target_dir(case_dir, category_key)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        source.replace(target)
        return target

    def list_uploaded_files(self, case_dir: Path) -> list[dict[str, object]]:
        raw_dir = case_dir / "raw"
        files: list[dict[str, object]] = []
        if not raw_dir.exists():
            return files

        for path in sorted(raw_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(case_dir)
            category = "/".join(rel.parts[1:-1]) if len(rel.parts) > 2 else rel.parts[1]
            files.append(
                {
                    "name": path.name,
                    "relative_path": str(rel),
                    "category_key": category,
                    "size_bytes": path.stat().st_size,
                }
            )
        return files

    def inspect_case(self, case_dir: Path) -> dict[str, object]:
        raw_dir = case_dir / "raw"
        category_counts: dict[str, int] = {}
        category_details: list[dict[str, object]] = []
        total_files = 0

        for category in RAW_CATEGORY_GROUPS:
            key = category["key"]
            if key == "05_检验检查":
                child_details: dict[str, int] = {}
                category_total = 0
                for child in category.get("children", []):
                    child_path = raw_dir / key / child
                    count = sum(1 for item in child_path.rglob("*") if item.is_file())
                    child_details[child] = count
                    category_total += count
                category_counts[key] = category_total
                category_details.append(
                    {
                        "key": key,
                        "label": category["label"],
                        "count": category_total,
                        "children": child_details,
                    }
                )
                total_files += category_total
                continue

            category_path = raw_dir / key
            count = sum(1 for item in category_path.rglob("*") if item.is_file())
            category_counts[key] = count
            category_details.append(
                {
                    "key": key,
                    "label": category["label"],
                    "count": count,
                }
            )
            total_files += count

        return {
            "case_dir": str(case_dir),
            "raw_dir": str(raw_dir),
            "workspace_dir": str(case_dir / "workspace"),
            "exports_dir": str(case_dir / "exports"),
            "total_files": total_files,
            "category_counts": category_counts,
            "categories": category_details,
            "missing_categories": [
                item["key"] for item in category_details if item["count"] == 0
            ],
            "files": self.list_uploaded_files(case_dir),
        }

    def run_scan(self, case_dir: Path) -> dict[str, object]:
        from case_organizer.cli import _scan_pipeline

        workspace_dir = case_dir / "workspace"
        manifest = _scan_pipeline(case_dir / "raw", workspace_dir)
        candidate_case_path = workspace_dir / "candidate_case.json"
        if candidate_case_path.exists():
            try:
                candidate_case = json.loads(candidate_case_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                candidate_case = {}
        else:
            candidate_case = {}
        return {
            "case_dir": str(case_dir),
            "workspace_dir": str(workspace_dir),
            "manifest": manifest,
            "manifest_path": str(workspace_dir / "manifest.json"),
            "candidate_case_path": str(workspace_dir / "candidate_case.json"),
            "candidate_case": candidate_case,
        }

    def export_summary(self, case_dir: Path) -> dict[str, Any]:
        exports_dir = case_dir / "exports"
        workspace_dir = case_dir / "workspace"
        summary: dict[str, Any] = {
            "case_dir": str(case_dir),
            "workspace_dir": str(workspace_dir),
            "exports_dir": str(exports_dir),
            "exports": {},
        }

        for group in EXPORT_GROUPS:
            group_dir = exports_dir / group
            summary["exports"][group] = {
                "path": str(group_dir),
                "exists": group_dir.exists(),
                "file_count": sum(1 for item in group_dir.rglob("*") if item.is_file()),
            }

        candidate_case_path = workspace_dir / "candidate_case.json"
        if candidate_case_path.exists():
            try:
                candidate_case = json.loads(candidate_case_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                candidate_case = {}
        else:
            candidate_case = {}

        summary["candidate_case"] = candidate_case
        summary["normalized_ready"] = (exports_dir / "normalized").exists()
        summary["legacy_ready"] = (exports_dir / "legacy").exists()
        bundle_path = exports_dir / "normalized" / "ca199_toolbox_bundle.json"
        summary["preferred_import"] = {
            "path": str(bundle_path),
            "exists": bundle_path.exists(),
        }
        return summary
