## 1. Prompt and Analysis Core

- [x] 1.1 Add helpers to load `assets/analyze_prompt.md` as a package resource
- [x] 1.2 Serialize the current session main and subagent logs into analysis content
- [x] 1.3 Build the full prompt by replacing `{{content}}` and marking truncated input when needed
- [x] 1.4 Implement temporary `mc --code -p -` execution with timeout and structured errors

## 2. Analyze API

- [x] 2.1 Add `POST /api/analyze` request parsing and session ID validation
- [x] 2.2 Return success JSON with report and elapsed time
- [x] 2.3 Return clear error JSON for missing session, missing `mc`, failed `mc`, empty output, and timeout

## 3. Web UI

- [x] 3.1 Add an "分析当前 Session" button that is enabled after loading a session
- [x] 3.2 Submit only the current session ID to `/api/analyze`
- [x] 3.3 Show loading, success report, and error states without persisting the report
- [x] 3.4 Reset transient analysis state when switching sessions
- [x] 3.5 Cache analysis reports in frontend memory by `sessionId`
- [x] 3.6 Add "查看分析报告" behavior to restore cached reports after viewing log details
- [x] 3.7 Add "重新分析" behavior that overwrites cached report only on success
- [x] 3.8 Preserve the old cached report and display an error when reanalysis fails
- [x] 3.9 Improve report Markdown rendering for headings, lists, tables, and code blocks
- [x] 3.10 Add report-specific styling for readable Markdown tables and code blocks
- [x] 3.11 Render Mermaid fenced code blocks as diagrams in analysis reports
- [x] 3.12 Add Mermaid fallback when the library is unavailable or rendering fails

## 4. Tests and Validation

- [x] 4.1 Add backend tests for prompt construction and current-session-only API behavior
- [x] 4.2 Add backend tests for `mc` failure and timeout handling
- [x] 4.3 Add frontend static regression tests for the analyze button and request shape
- [x] 4.4 Run unittest, py_compile, diff check, and OpenSpec strict validation
- [x] 4.5 Add frontend regression tests for report cache, restore, and reanalysis behavior
- [x] 4.6 Re-run unittest, py_compile, diff check, and OpenSpec strict validation
- [x] 4.7 Add frontend regression tests for enhanced Markdown report rendering
- [x] 4.8 Re-run unittest, py_compile, diff check, and OpenSpec strict validation
- [x] 4.9 Add frontend regression tests for Mermaid report rendering and fallback
- [x] 4.10 Re-run unittest, py_compile, diff check, and OpenSpec strict validation
