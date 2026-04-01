"""Local readers for plain text and simple tabular inputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class LocalReadResult:
    """Unified payload for local text/table readers."""

    text_content: str
    reader: str
    tables: list[dict] = field(default_factory=list)
    source_path: str | None = None


def read_local_text(path: Path) -> LocalReadResult:
    """Read UTF-8 plain text or markdown as-is."""

    return LocalReadResult(
        text_content=path.read_text(encoding="utf-8"),
        reader="local_text",
        source_path=str(path),
    )


def read_local_csv(path: Path) -> LocalReadResult:
    """Read a CSV file into markdown-like text and row records."""

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    table_lines = [", ".join(fieldnames)] if fieldnames else []
    for row in rows:
        table_lines.append(", ".join((row.get(name, "") or "").strip() for name in fieldnames))

    return LocalReadResult(
        text_content="\n".join(table_lines),
        reader="local_csv",
        tables=[{"name": path.name, "rows": rows, "columns": fieldnames}],
        source_path=str(path),
    )


def read_local_spreadsheet(path: Path) -> LocalReadResult:
    """Read an xls/xlsx file using pandas when available."""

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("Reading spreadsheet files requires pandas to be installed.") from exc

    frames = pd.read_excel(path, sheet_name=None)
    tables: list[dict] = []
    text_blocks: list[str] = []

    for sheet_name, frame in frames.items():
        rows = frame.fillna("").to_dict(orient="records")
        columns = list(frame.columns)
        tables.append({"name": sheet_name, "rows": rows, "columns": columns})
        text_blocks.append(f"[{sheet_name}]")
        text_blocks.append(frame.fillna("").to_csv(index=False))

    return LocalReadResult(
        text_content="\n".join(text_blocks).strip(),
        reader="local_spreadsheet",
        tables=tables,
        source_path=str(path),
    )


def read_local_file(path: Path) -> LocalReadResult:
    """Dispatch to the appropriate local reader based on file suffix."""

    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return read_local_text(path)
    if suffix == ".csv":
        return read_local_csv(path)
    if suffix in {".xls", ".xlsx"}:
        return read_local_spreadsheet(path)

    raise ValueError(f"Unsupported local file type: {suffix}")
