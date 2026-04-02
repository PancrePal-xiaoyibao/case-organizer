# Quick Start

## Recommended Flow

`case-organizer` is now designed to work together with `ca199-toolbox-v2`.

The recommended output is:

```text
exports/normalized/ca199_toolbox_bundle.json
```

This file is the preferred handoff into `ca199-toolbox-v2`.

## 1. Install

```bash
cd case-organizer
python -m pip install -e ".[dev]"
```

## 2. Configure MinerU

Create `.env` in the project root:

```env
MINERU_API_TOKEN=your_token
MINERU_RESULTS_BASE=https://mineru.net/api/v4
```

If MinerU is not configured, local text and CSV readers still work, but PDF/image parsing will not use the remote extraction path.

## 3. Create A Case Directory

```bash
python -m case_organizer.cli init ./output/patient001
```

This creates:

```text
./output/patient001/
  raw/
  workspace/
  exports/
```

## 4. Add Files

Place patient files into matching `raw/` subdirectories, for example:

- `raw/03_影像报告/`
- `raw/04_病理与基因/`
- `raw/06_处方与用药/`
- `raw/99_待分类/`

## 5. Run The Wizard

```bash
python -m case_organizer.cli review ./output/patient001/workspace --host 127.0.0.1 --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

The wizard supports:

1. Create a case
2. Upload multiple files per category
3. Inspect file completeness
4. Run scan
5. Review candidate output
6. Check export summaries

Upload limits:

- multiple files supported
- max size: `10MB` per file

## 6. Preferred Export

After scan/export, use:

```text
exports/normalized/ca199_toolbox_bundle.json
```

This is the preferred import file for `ca199-toolbox-v2`.

## 7. CLI Scan Only

```bash
python -m case_organizer.cli scan ./output/patient001
```

## 8. Tests

```bash
pytest -q
```

## 9. Team Docs

For team onboarding, read:

- [README.md](README.md)
- [docs/TEAM_HANDOFF.md](docs/TEAM_HANDOFF.md)
- [docs/output-contract.md](docs/output-contract.md)
