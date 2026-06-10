## 1. Package format and export flow

- [x] 1.1 Redesign exporter package layout to store each session under `sessions/<session-id>/`
- [x] 1.2 Generate a package-level manifest v2 with per-session metadata, included flags, and counts
- [x] 1.3 Update default filename generation for single-session and multi-session exports
- [x] 1.4 Update README and export summaries to describe package-wide import behavior

## 2. Import compatibility and safety

- [x] 2.1 Refactor import parsing to support manifest v2 multi-session packages
- [x] 2.2 Keep backward compatibility for legacy single-session packages
- [x] 2.3 Improve archive extraction to use safe member validation and generic tar read mode
- [x] 2.4 Prompt once for overwrite when any target session already exists, with `--force` bypass

## 3. Integration surfaces

- [x] 3.1 Update CLI export/import messaging to reflect package-wide multi-session behavior
- [x] 3.2 Update viewer `/api/export` to generate filenames and package content consistent with manifest v2
- [x] 3.3 Update the Web UI export modal text and default filename handling to stay aligned with the new package format
- [x] 3.4 Update the Web UI export modal to support selecting and exporting multiple sessions

## 4. Regression tests

- [x] 4.1 Add exporter tests for single-session and multi-session archive structure and manifest contents
- [x] 4.2 Add import tests for multi-session package import, overwrite behavior, and legacy package compatibility
- [x] 4.3 Run the relevant automated tests and verify they pass
- [x] 4.4 Verify Web UI multi-session export behavior
