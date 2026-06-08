## Why

The project is currently shaped around an internal `deep-ai-analysis` + `mc` workflow with a hard-coded internal model API domain. To become a usable open-source tool, it needs a public `ccwhat` identity, a safe first-run experience, and a recording setup that works for official Claude Code, third-party gateways, and user-defined model API endpoints without silently capturing unrelated traffic.

## What Changes

- **BREAKING** Rename the public package, module, CLI command, data directories, export package names, and user-facing copy from `deep-ai-analysis` / `deep_ai_analysis` to `ccwhat`.
- **BREAKING** Replace the `start-mc` product entry point with a generic `run` command that can launch Claude Code or any user-provided AI coding CLI with proxy and CA environment variables injected.
- Add a first-run terminal onboarding wizard that guides users through official Claude API, gateway/base-url, or discovery-based setup.
- Add metadata-only discovery that observes hosts, paths, methods, status codes, and content types to suggest model API domains, without saving request/response bodies.
- Make recorded domains and paths user-configurable via CLI options and persisted config, with safe presets for common Claude Code usage.
- Tighten recording safety defaults: domain allowlist required, model-API path/content-type filtering, broader header redaction, body-size limits, and clearer terminal warnings.
- Update Web viewer UI to show current recording configuration, recording health, and actionable empty states when no model traffic is captured.
- Remove internal install links, internal sample data, and internal release assumptions from public-facing docs and packaging.

## Capabilities

### New Capabilities
- `project-branding`: Public `ccwhat` naming, package metadata, local directory names, export package names, and public install/documentation contracts.
- `cli-run-command`: Generic command launcher that injects proxy/CA environment variables and replaces the internal `start-mc` workflow for normal users.
- `first-run-onboarding`: First-run terminal wizard for choosing official Claude API, gateway/base-url, or discovery setup and saving config.
- `recording-discovery`: Metadata-only traffic discovery that recommends recordable model API endpoints without storing sensitive payloads.
- `recording-config`: Persisted user configuration for presets, allowlisted domains, path filters, redaction, size limits, and setup state.
- `public-release-readiness`: Public repository, README, release checklist, and build artifact requirements for the first open-source release.

### Modified Capabilities
- `cli-framework`: Rename the CLI entry point and help/version text to `ccwhat`; register new `run`, `setup`, and `discover` commands; deprecate `start-mc`.
- `proxy-interceptor`: Replace hard-coded `api.example.com` filtering with config-driven allowlists, path/content-type filters, broader redaction, and safer fallback session IDs.
- `session-viewer`: Show active recording config and better empty/error states for first-time users and gateway users.
- `start-mc`: Remove the internal `mc --code` launcher requirement from the public workflow and migrate users to `ccwhat -- <command...>`.
- `start-mc-passthrough`: Remove `start-mc` passthrough behavior and migrate passthrough semantics to `ccwhat run`.
- `export-command`: Rename export destinations and copy to `ccwhat`; keep compatibility with legacy import where practical.
- `import-command`: Accept new `ccwhat-export` packages and legacy `deep-ai-analysis-export` packages.
- `export-package-structure`: Rename package root and generated helper scripts to `ccwhat` while preserving migration compatibility.
- `export-manifest`: Identify exported packages as `ccwhat` packages and include enough tool metadata for compatibility checks.
- `export-web-ui`: Update visible commands and copy from `deep-ai-analysis` to `ccwhat`.

## Impact

- Affected code: `pyproject.toml`, package/module layout, CLI command modules, proxy addon/config, analyzer launcher, exporter/importer, viewer server, `viewer/*.html`, tests, README, install/release docs.
- Affected user workflows: install, first run, proxy launch, AI coding CLI launch, discovery, export/import, viewer troubleshooting.
- Affected local files: default config/data path changes from `~/.deep-ai-analysis` to `~/.ccwhat`; legacy paths should remain readable for migration.
- Security/privacy impact: recording becomes opt-in by allowlist, discovery stores only metadata, and logs redact more sensitive headers by default.
