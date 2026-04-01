# Case Organizer Output Contract

`case-organizer` writes a workspace directory that acts as the file-level interface to `ca199_toolbox`.

## Required files

The downstream contract only depends on files under `workspace/normalized/`:

```text
workspace/
  normalized/
    indicators.csv
    medications.csv
    timeline_events.csv
    patient_summary.json
    standard_case.json
```

## File meanings

`indicators.csv`
Normalizes tumor markers and other extracted lab-like indicators into one row per measurement.

`medications.csv`
Normalizes treatment phases and regimen metadata into one row per phase.

`timeline_events.csv`
Normalizes key clinical events, notes, and patient comments into a chronological event log.

`patient_summary.json`
Provides the compact summary used by `ca199_toolbox` for overview cards and printable summaries.

`standard_case.json`
Contains the full structured case model for future consumers and debugging.

## Workspace metadata

The workspace root also includes:

```text
workspace/
  manifest.json
  candidate_case.json
  file_index.json
```

`manifest.json`
Tracks the input directory, processed files, deferred MinerU files, and output locations.

`candidate_case.json`
Stores the reviewable candidate payload before the final normalization step is approved.

`file_index.json`
Stores incremental fingerprints for source files so unchanged files are skipped on later runs.

## Contract rules

1. `ca199_toolbox` must read only the normalized outputs and not depend on internal parsing state.
2. The `normalized/` directory is the stable handoff point between the two projects.
3. The structure and headers of `indicators.csv`, `medications.csv`, and `timeline_events.csv` are versioned contract data.
4. The workspace may contain additional debug or cache files, but downstream consumers must ignore them.

## Versioning rule

When the output contract changes, update this document and the `ca199_toolbox` reader at the same time.
