# Case Organizer

`case-organizer` is a local-first, single-patient case intake and normalization tool.

It helps patients and caregivers organize medical files into a fixed directory structure, extract content with MinerU or local readers, review a candidate case summary, and export normalized files for `ca199_toolbox`.

## Product Boundary

- single patient only
- one case directory per patient
- local-first by default
- not a multi-patient case management system

## Default Case Root

By default, new cases are created under:

```text
./output/
```

Example:

```text
./output/patient001
```

You can override the root with:

```bash
CASE_ORGANIZER_CASE_ROOT=/custom/path
```

## Recommended Case Layout

```text
output/
  patient001/
    raw/
      01_基本资料/
      02_诊断报告书/
      03_影像报告/
      04_病理与基因/
      05_检验检查/
        01_肿瘤标志物/
        02_血常规/
        03_肝肾功能/
        04_凝血/
        05_炎症指标/
        06_体液检查_尿便常规/
        07_其他检验/
      06_处方与用药/
      07_个人病情记录/
      08_手术与住院资料/
      99_待分类/
    workspace/
    exports/
      normalized/
      legacy/
      printable/
      summaries/
```

Directory responsibilities:

- `raw/`: original files placed by the patient or caregiver
- `workspace/`: generated indexes, extraction artifacts, candidate case, and normalized working outputs
- `exports/`: final outputs for downstream use, printing, and summaries

## Supported Inputs

- images: `jpg`, `jpeg`, `png`, `webp`
- documents: `pdf`, `doc`, `docx`
- spreadsheets: `xls`, `xlsx`, `csv`
- text: `txt`, `md`

## What It Does

1. initializes a fixed single-patient directory tree
2. scans files recursively inside `raw/`
3. extracts text and structure via MinerU or local readers
4. builds a candidate case model for review
5. exposes a local web wizard for guided use
6. exports:
   - `normalized/`
   - `legacy/`
   - `printable/`
   - `summaries/`

## Commands

```bash
cd case-organizer
python -m case_organizer.cli init ./output/patient001
python -m case_organizer.cli scan ./output/patient001
python -m case_organizer.cli review ./output/patient001/workspace
```

## Web Wizard

Launch the local patient wizard:

```bash
cd case-organizer
python -m case_organizer.cli review ./output/patient001/workspace --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765
```

Current wizard capabilities:

- create case directories
- upload multiple files to a category
- max upload size: `10MB` per file
- inspect uploaded files
- reassign or delete uploaded files
- run scan
- inspect candidate output
- inspect export group status

## Output Contract

The long-term interface for `ca199_toolbox` is:

- `exports/normalized/`

The compatibility layer for the legacy `ca199_toolbox` page is:

- `exports/legacy/`

See [docs/output-contract.md](docs/output-contract.md) for the current file contract.

## Additional Docs

- Chinese README: [README_CN.md](README_CN.md)
- Quick start: [QUICK_START.md](QUICK_START.md)

## Development

```bash
cd case-organizer
python -m pip install -e ".[dev]"
pytest -q
```
