## 1. Repository Hygiene and Public Naming

- [x] 1.1 Audit tracked files for internal domains, tokens, private paths, notebooks, captured logs, and proprietary business samples.
- [x] 1.2 Remove or sanitize internal sample data, notebooks, diagnostic logs, and private release docs from the public repository.
- [x] 1.3 Update `.gitignore` to exclude `.ccwhat/`, `.deep-ai-analysis/`, raw captures, generated exports, wheels, build outputs, notebook scratch files, and local diagnostic data.
- [x] 1.4 Rename Python package directory and imports from `deep_ai_analysis` to `ccwhat`.
- [x] 1.5 Update `pyproject.toml` distribution metadata to package name `ccwhat`, script `ccwhat`, and package-data paths.
- [x] 1.6 Update version sourcing so `ccwhat --version` matches `pyproject.toml`.
- [x] 1.7 Replace user-facing `deep-ai-analysis` copy with `ccwhat` in CLI help, viewer copy, README, export README, install docs, and tests.
- [x] 1.8 Confirm no top-level `cc` console command is registered or documented.

## 2. Configuration Model

- [x] 2.1 Add config load/save module for `~/.ccwhat/config.toml` with optional config path override.
- [x] 2.2 Define recording config model for preset, domains, paths, max body bytes, redaction headers, redaction header-name patterns, and onboarding state.
- [x] 2.3 Implement Claude preset expansion to `api.anthropic.com` with `/v1/messages` and `/v1/messages/count_tokens`.
- [x] 2.4 Implement validation for empty allowlists, malformed domains, path normalization, and invalid body limits.
- [x] 2.5 Add legacy path fallback/migration helpers for reading existing `~/.deep-ai-analysis` data where needed.
- [x] 2.6 Add unit tests for config defaults, validation, CLI overrides, and persisted TOML output.

## 3. First-Run Onboarding

- [x] 3.1 Implement `ccwhat setup` interactive wizard with official Claude API, gateway/base URL, and discovery modes.
- [x] 3.2 Detect candidate gateway hosts from `ANTHROPIC_BASE_URL`, `ANTHROPIC_BEDROCK_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL`, and `ANTHROPIC_AWS_BASE_URL`.
- [x] 3.3 Show confirmation screen with exact domains, paths, redaction summary, body size limit, and privacy boundary copy.
- [x] 3.4 Save onboarding completion state and selected recording config to `~/.ccwhat/config.toml`.
- [x] 3.5 Support non-interactive `ccwhat setup --preset ... --yes` and `ccwhat setup --domain ... --path ... --yes`.
- [x] 3.6 Add tests for first-run setup, existing-config setup, invalid non-interactive input, and no-change flow.

## 4. Metadata-Only Discovery

- [x] 4.1 Implement discovery mode that starts a proxy without persisting request/response payloads.
- [x] 4.2 Capture only host, method, path, status code, request/response content type, timestamp, streaming flag, and redacted sensitive-header presence.
- [x] 4.3 Score candidates for Anthropic Messages paths and streaming model responses, with human-readable recommendation reasons.
- [x] 4.4 Implement `ccwhat discover` for standalone proxy discovery.
- [x] 4.5 Implement `ccwhat discover -- <command...>` to run target commands through discovery proxy.
- [x] 4.6 Prompt users to confirm discovered candidates and save selected config.
- [x] 4.7 Add tests that discovery never stores payload bodies or sensitive header values.

## 5. Proxy Recording Safety

- [x] 5.1 Replace hard-coded `api.example.com` defaults with config/CLI/preset-driven domain allowlists.
- [x] 5.2 Add `--domain`, `--path`, `--preset`, `--config`, and save/override behavior to `ccwhat proxy`.
- [x] 5.3 Require a valid allowlist before payload recording; trigger onboarding in interactive mode and fail safely in non-interactive mode.
- [x] 5.4 Apply path/content-type filtering so configured domains do not automatically record unrelated routes.
- [x] 5.5 Expand request and response header redaction to configured headers and header-name patterns.
- [x] 5.6 Add request/response body size limiting with truncation metadata.
- [x] 5.7 Generate local session IDs for requests without `X-Claude-Code-Session-Id` instead of writing all unknown traffic to `unknown`.
- [x] 5.8 Update SSE recording to use the same filtering, redaction, size limits, and session fallback.
- [x] 5.9 Add tests for domain allowlists, empty allowlist behavior, redaction, body truncation, local session IDs, and SSE handling.

## 6. Generic Run Command

- [x] 6.1 Implement `ccwhat run -- <command...>` command parsing with exact argument passthrough.
- [x] 6.2 Make `run` start a managed proxy when no compatible proxy is running on the configured port.
- [x] 6.3 Make `run` reuse an existing compatible ccwhat proxy when available.
- [x] 6.4 Inject `HTTPS_PROXY`, `HTTP_PROXY`, `NODE_EXTRA_CA_CERTS`, and configured certificate variables while preserving unrelated environment variables.
- [x] 6.5 Preserve `NO_PROXY` unless the user explicitly configures an override.
- [x] 6.6 Ensure managed proxy cleanup and target exit-code propagation on normal exit and Ctrl+C.
- [x] 6.7 Integrate `run` with first-run onboarding and `--no-setup`.
- [x] 6.8 Remove `start-mc` from public help or convert it to a deprecated hidden alias that prints migration guidance.
- [x] 6.9 Add tests for command passthrough, missing command, env injection, proxy lifecycle, existing proxy reuse, and deprecated `start-mc`.

## 7. Viewer UX and Status API

- [x] 7.1 Add `GET /api/recording/status` with active domains, path filters, config path, raw log dir, latest raw log timestamp, and config validity.
- [x] 7.2 Ensure status API never returns API keys, authorization values, cookies, or unredacted sensitive header values.
- [x] 7.3 Add viewer recording status panel showing current domains, paths, log directory, config path, redaction summary, and latest record time.
- [x] 7.4 Add actionable empty states for missing raw logs, gateway users, domain mismatch, CA trust issues, and not launching through `ccwhat run`.
- [x] 7.5 Update viewer visible commands and copy to `ccwhat`.
- [x] 7.6 Add backend and frontend tests or fixture assertions for status API, empty-state copy, and command copy.

## 8. Export and Import Migration

- [x] 8.1 Rename default export directory to `~/Downloads/ccwhat-exports/`.
- [x] 8.2 Rename default import directory to `~/Downloads/ccwhat-imports/`.
- [x] 8.3 Change export package root to `ccwhat-export/`.
- [x] 8.4 Update exported README and `view.command` to use `ccwhat import . --open`.
- [x] 8.5 Add `toolName: "ccwhat"` and current manifest metadata while preserving existing session/content summaries.
- [x] 8.6 Make `ccwhat import` accept both `ccwhat-export/` and legacy `deep-ai-analysis-export/` roots.
- [x] 8.7 Update Web export modal command copy and package copy to `ccwhat`.
- [x] 8.8 Add tests for new export structure, legacy import compatibility, export command copy, and import overwrite behavior.

## 9. Documentation and Release Readiness

- [x] 9.1 Rewrite README around the shortest Claude quick start as the primary quick start.
- [x] 9.2 Document setup modes: official Claude API, gateway/base URL, and discovery.
- [x] 9.3 Document privacy boundaries, MITM certificate setup, header redaction, body truncation, and local-only logging.
- [x] 9.4 Document advanced split commands: `ccwhat setup`, `ccwhat proxy`, `ccwhat discover`, `ccwhat web`, `ccwhat export`, and `ccwhat import`.
- [x] 9.5 Replace internal install script references with public pip/pipx/source install instructions.
- [x] 9.6 Add public release checklist for PyPI/GitHub Releases and remove internal S3 release instructions.
- [x] 9.7 Replace README placeholder repository URLs with the real public GitHub repository URL.
- [x] 9.8 Make README the public first-run source of truth: include supported install methods, `ccwhat -- <cli>`, custom gateway/domain setup, discovery mode, privacy boundaries, and troubleshooting links.
- [x] 9.9 Remove or sanitize remaining public docs that still mention internal object storage, internal domains, private paths, old wheel names, or old package names.
- [x] 9.10 Align release checklist commands with declared dependencies, using either `python -m unittest discover -v` or an explicitly declared `pytest` dev dependency.
- [x] 9.11 Add a final public-release scan step that fails if tracked files contain internal domains, private user paths, real tokens, old package distribution names, or local diagnostic captures.

## 10. Verification

- [x] 10.1 Run OpenSpec validation for this change.
- [x] 10.2 Run the full Python test suite.
- [x] 10.3 Run CLI smoke tests for `ccwhat --help`, `ccwhat setup --preset claude --yes`, `ccwhat proxy --help`, `ccwhat run --help`, `ccwhat discover --help`, `ccwhat export --help`, and `ccwhat import --help`.
- [x] 10.4 Manually verify first-run onboarding in a clean home directory.
- [x] 10.5 Manually verify metadata-only discovery with a fake or fixture HTTP client.
- [x] 10.6 Manually verify viewer status and empty-state UX in the browser.
- [x] 10.7 Re-run repository scan for internal domains, tokens, private paths, and generated logs before public release.
- [x] 10.8 Verify `git ls-files` no longer includes `deep_ai_analysis/`, `deep_ai_analysis.egg-info/`, `sample_data/`, generated exports, internal notebooks, or private diagnostic docs.
- [x] 10.9 Verify source distribution and wheel contain only public packages (`ccwhat*`, `viewer*`) and no legacy package tree or sample captures.
- [x] 10.10 Verify `ccwhat run` fails clearly and cleans marker files when the managed proxy process exits before binding its port.
- [x] 10.11 Verify `ccwhat run` refuses to reuse an occupied port unless the marker identifies a live compatible ccwhat-managed proxy.

## 11. Review Follow-up: Public Release Blockers

- [x] 11.1 Remove the tracked legacy `deep_ai_analysis/` package tree from the public release commit; `.gitignore` alone is insufficient for already-tracked files.
- [x] 11.2 Confirm deleted `sample_data/` files are staged as removals and do not appear in the release commit.
- [x] 11.3 Delete or rewrite `docs/打包发布.md`, `docs/mitmproxy-addon-import-issue.md`, internal notebooks, and any private diagnostic reports before publication.
- [x] 11.4 Keep only intentional legacy compatibility references, such as legacy import-package support and legacy config migration; document why each remaining `deep-ai-analysis` or `.deep-ai-analysis` reference is allowed.
- [x] 11.5 Harden managed proxy startup so marker files are written only after compatibility can be established, or are removed immediately on failed startup.
- [x] 11.6 Add tests covering failed managed-proxy startup, stale marker cleanup, occupied non-ccwhat port refusal, and compatible proxy reuse.
- [x] 11.7 Re-run the complete release verification after these blockers are fixed and update this task list before tagging the first public release.

## 12. One-Command Viewer Launch

- [x] 12.1 Update `cli-run-command` spec so `ccwhat run -- <command>` starts or reuses the viewer and opens the browser by default.
- [x] 12.2 Add `ccwhat run` options to disable viewer launch and choose the viewer port.
- [x] 12.3 Start the viewer in-process as a managed background server when the viewer port is free, and shut it down when the target command exits.
- [x] 12.4 If the viewer port is already occupied, print and open the viewer URL instead of failing the run command.
- [x] 12.5 Make `ccwhat web` handle an occupied viewer port by opening/printing the existing viewer URL instead of showing a low-level bind error.
- [x] 12.6 Update English and Chinese README files so the one-line run command explains that the browser opens automatically and can be reopened with `ccwhat web`.
- [x] 12.7 Add focused tests for managed viewer startup, `--no-web`, viewer-port reuse, and `ccwhat web` occupied-port behavior.

## 13. Claude Shortcut Command (Superseded by 14)

- [x] 13.1 Update CLI spec to define `ccwhat --claude` as the shortest public Claude Code launch path.
- [x] 13.2 Implement `ccwhat --claude` by invoking the existing `run` command with target command `claude`.
- [x] 13.3 Keep `ccwhat run -- <command>` for custom CLI launches and advanced flags.
- [x] 13.4 Update English and Chinese README files to use `ccwhat --claude` as the primary run command.
- [x] 13.5 Update setup/discovery/deprecated command hints and focused tests for the shortcut.

## 14. Generic Top-Level Passthrough

- [x] 14.1 Replace the Claude-only shortcut with generic top-level passthrough: `ccwhat -- <cli> [args...]`.
- [x] 14.2 Keep `run` as a hidden compatibility command, but remove it from public quick-start and common command copy.
- [x] 14.3 Support top-level launch options such as `--no-web`, `--port`, `--web-port`, `--output`, `--config`, and `--no-setup` before the `--` separator.
- [x] 14.4 Preserve arbitrary target CLI arguments after `--`, including flags such as `mc --code`.
- [x] 14.5 Update English and Chinese README files to explain the generic command style.
- [x] 14.6 Update setup/discovery/deprecated command hints and focused tests for generic passthrough.

## 15. Report Analyzer Uses Launched CLI

- [x] 15.1 Update session-viewer spec so reports generated from a viewer started by `ccwhat -- <cli>` use that same `<cli>` command.
- [x] 15.2 Pass the top-level target command from `run` into the managed viewer server as the analysis command.
- [x] 15.3 Update analyzer helper to accept an explicit command for report generation while keeping existing environment/default fallback for standalone viewer use.
- [x] 15.4 Add focused tests that report generation invokes the provided command and that manual domain/path setup remains the supported gateway path.
