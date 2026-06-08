## Context

The current project is a Python Click CLI plus mitmproxy addon and static HTML viewer. It assumes an internal workflow: `deep-ai-analysis proxy`, `deep-ai-analysis start-mc`, a hard-coded `api.example.com` recording domain, `mc --code` as the launcher/analyzer, and local paths under `~/.deep-ai-analysis`. The viewer is valuable, but ordinary open-source users will likely run official Claude Code, a third-party gateway, LiteLLM, OpenRouter-compatible routes, or a private Anthropic-compatible base URL.

The primary product risk is capturing too much. Claude Code can use standard proxy environment variables, but it also makes non-model network requests for auth, updates, plugins, WebFetch, telemetry, and gateways. The open-source UX must help users find the model API endpoint while requiring an allowlist before payload recording starts.

## Goals / Non-Goals

**Goals:**
- Establish `ccwhat` as the public product, CLI, module, local data path, export package root, and visible copy.
- Make `ccwhat -- <command...>` the main user path for launching an AI coding CLI with proxy and CA variables.
- Provide a first-run terminal wizard that configures recording without requiring users to understand domains upfront.
- Support official Claude API, custom Anthropic-compatible gateways, and unknown setups through metadata-only discovery.
- Keep recording opt-in by allowlisted host/path and safe by default through broader redaction and size limits.
- Give clear terminal and viewer feedback about what is being recorded and why no records appear.
- Preserve practical import compatibility for existing `deep-ai-analysis-export` diagnostic packages.

**Non-Goals:**
- Do not build a hosted service, account system, cloud sync, or remote telemetry.
- Do not make the Web viewer a full configuration editor in this change; setup remains CLI-first.
- Do not guarantee perfect provider detection for every AI coding tool; discovery produces candidates, not automatic recording rules.
- Do not parse every provider's response format into a normalized semantic trace in this change.
- Do not keep `cc` as the public CLI name because it conflicts with common system compiler commands.

## Decisions

### 1. CLI-first onboarding with a guided terminal UI

Use a terminal wizard triggered by `ccwhat setup`, by first `ccwhat -- ...`, or by `ccwhat proxy` when no recording config exists.

Main flow:

```text
ccwhat -- claude
└─ no config
   └─ setup wizard
      ├─ official Claude API -> api.anthropic.com + /v1/messages preset
      ├─ gateway/base URL -> parse ANTHROPIC_BASE_URL or prompt for URL
      └─ not sure -> metadata-only discovery
```

Rationale: this keeps the first successful experience to one command while avoiding unsafe automatic recording. A Web-only setup would require users to start the server before the core proxy problem is solved.

Alternative considered: pure auto-detection. Rejected because it can capture auth/update/GitHub/MCP/WebFetch traffic and does not know whether a shared gateway host should be recorded.

### 2. Explicit recording config is required for payload capture

Recording request/response bodies requires at least one configured allowlisted domain. Discovery may run without config, but only stores metadata: host, method, path, status, content type, timestamp, and candidate score/reason.

Rationale: users can safely run discovery in unknown environments. Payload capture remains a conscious action.

Alternative considered: record all proxied hosts and filter in the viewer. Rejected because sensitive data would already be written to disk.

### 3. Presets are suggestions, not hidden policy

Provide named presets such as `claude` that expand to visible domain/path rules:

```text
domain: api.anthropic.com
paths: /v1/messages, /v1/messages/count_tokens
```

Gateway setups derive a host from `ANTHROPIC_BASE_URL`, `ANTHROPIC_BEDROCK_BASE_URL`, `ANTHROPIC_VERTEX_BASE_URL`, or `ANTHROPIC_AWS_BASE_URL` when present, but the user confirms before saving.

Rationale: official Claude Code users get a simple default, while gateway users avoid hand-editing config. The UI always shows what will be recorded.

### 4. `run` replaces `start-mc`, legacy alias optional

`ccwhat -- <command...>` launches any command with:

```text
HTTPS_PROXY=http://127.0.0.1:<port>
HTTP_PROXY=http://127.0.0.1:<port>
NODE_EXTRA_CA_CERTS=<mitmproxy-ca-cert.pem>
SSL_CERT_FILE=<mitmproxy-ca-cert.pem> when requested/configured
```

The command should start a managed local proxy on the configured port when one is not already available, then stop that managed proxy when the launched command exits. If a compatible proxy is already running, `run` should reuse it and avoid starting a duplicate process.

`start-mc` is not a normal open-source workflow. It can remain as a hidden/deprecated compatibility alias during migration, but help and docs must point to `run`.

Rationale: ordinary users may run `claude`, `codex`, `cursor-agent`, or custom wrappers. The tool's job is traffic capture, not choosing the coding assistant.

### 5. Persisted config lives under `~/.ccwhat`

Use `~/.ccwhat/config.toml` for user configuration and `~/.ccwhat/raw-req-resp/` for logs. Read legacy `~/.deep-ai-analysis` locations only for migration/import compatibility.

Proposed config shape:

```toml
[recording]
preset = "claude"
domains = ["api.anthropic.com"]
paths = ["/v1/messages", "/v1/messages/count_tokens"]
max_body_bytes = 5242880

[redaction]
headers = ["authorization", "cookie", "set-cookie", "x-api-key", "proxy-authorization"]
header_name_patterns = ["token", "secret", "key"]

[onboarding]
completed = true
last_mode = "official-claude"
```

Rationale: TOML is readable and suitable for manual edits without requiring a heavy settings dependency. Python 3.11 has `tomllib`; Python 3.10 can use a lightweight fallback or simple writer for the limited shape.

### 6. Viewer shows recording state, not full setup editing

The viewer top area should show:
- active recording domains/paths,
- raw log directory,
- latest recorded request time,
- empty-state guidance,
- commands to run setup or discovery.

Rationale: users often discover misconfiguration only after opening the viewer. Showing active config and targeted next steps reduces confusion while avoiding a complex write-capable web settings UI.

### 7. Export/import supports new names and legacy packages

New packages use `ccwhat-export/`, generated README copy references `ccwhat`, and helper scripts call `ccwhat import`. Import MUST continue to accept legacy `deep-ai-analysis-export/` package roots where possible.

Rationale: renaming should not strand previously generated diagnostic packages.

### 8. Public release is gated by tracked-file hygiene

Before the first public push or release tag, the repository state must be checked from Git's tracked-file view, not only from filesystem ignores. `.gitignore` prevents future accidental additions, but already-tracked legacy packages, internal docs, notebooks, sample captures, or generated exports must be deleted or removed from tracking in the release commit.

The release checklist should be executable in a clean environment using commands supported by declared dependencies. If the project uses `unittest`, the checklist should call `python -m unittest discover -v`; if it uses `pytest`, `pytest` must be declared in a dev/test extra.

Rationale: open-source users and downstream packagers consume committed files and built artifacts, not local ignore rules.

### 9. Managed proxy compatibility is explicit

`ccwhat run` may reuse an already-running proxy only when compatibility can be established. A marker file is acceptable as a lightweight compatibility signal, but startup and reuse must also handle stale markers, dead PIDs, occupied non-ccwhat ports, and managed proxy processes that exit before binding the configured port.

Rationale: proxy environment variables affect every launched AI coding CLI request. Reusing the wrong process or launching with a dead proxy produces confusing failures and can route sensitive traffic through an unintended local service.

## Risks / Trade-offs

- **Risk: first-run wizard blocks scripted usage** -> Provide `--no-setup`, `--yes`, `--domain`, `--preset`, and config-file paths for non-interactive runs.
- **Risk: discovery misses non-Anthropic-compatible gateways** -> Show all observed hosts with reason labels, allow manual `ccwhat setup --domain <host>`, and document path override.
- **Risk: users think discovery captured payloads** -> Terminal copy must say discovery stores metadata only; viewer should label discovered candidates separately from recorded logs.
- **Risk: breaking imports and docs through rename** -> Keep legacy import support and add migration tests for old export packages and old config/log directories.
- **Risk: TOML writing on Python 3.10 adds dependency complexity** -> Keep writer simple or add a small dependency only if the implementation needs comments/round-trip preservation.
- **Risk: broader redaction hides debugging details** -> Redaction affects headers only by default; body redaction is out of scope except body size limits and documented warnings.

## Migration Plan

1. Introduce `ccwhat` package/script while tests still validate existing behavior through updated names.
2. Add config loading with legacy path fallback.
3. Implement `run`, `setup`, and `discover`; mark `start-mc` deprecated or remove it from public help.
4. Change proxy defaults from internal hard-coded domain to config-driven allowlists.
5. Rename export/import package roots and maintain legacy package import.
6. Update viewer copy and status panels.
7. Remove or sanitize internal docs/sample data before public release.
8. Verify tracked-file hygiene, README accuracy, release checklist commands, built artifacts, and proxy startup failure behavior before tagging the first public release.

Rollback strategy: preserve a compatibility branch/tag before rename. Because public CLI/module names are breaking, rollback is source-level rather than runtime feature-flag based.

## Open Questions

- Should `SSL_CERT_FILE` be injected by default, or only when users enable it? Node-based Claude Code mainly needs `NODE_EXTRA_CA_CERTS`, but Python-based tools may need `SSL_CERT_FILE`.
- Which presets beyond `claude` should ship initially? The safest initial scope is `claude` plus manual/gateway setup.
