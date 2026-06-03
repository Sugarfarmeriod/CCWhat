# ccwhat

Record and view AI coding CLI traffic locally.

English | [中文](README.zh.md)

## Quick start

Install or update:

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash
```

Run:

```bash
ccwhat -- claude
```

Uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash -s -- uninstall
```

The first run will guide you through what model API domain to record. Direct Claude users can choose the Claude preset. Gateway or relay users can enter their own domain, or use discovery mode when unsure.

## What it does

`ccwhat -- claude` starts a local proxy, launches Claude Code through it, records only the domains/paths you confirmed, and stores logs under `~/.ccwhat/`.

It also opens the viewer in your browser. If you close the tab, reopen it with:

```bash
ccwhat web
```

## Notes

- Supports macOS, Linux, and WSL. Windows native is not supported yet.
- Python 3.10+ and mitmproxy are required; the install script checks them.
- HTTPS recording requires trusting the mitmproxy CA certificate when prompted.
- Authorization, cookies, API keys, token/secret/key headers are redacted.
- Discovery mode stores metadata only, not request or response bodies.

## Useful commands

```bash
ccwhat setup              # change recording config
ccwhat discover -- claude # find the API endpoint without storing payloads
ccwhat --no-web -- claude
ccwhat -- mc --code       # launch any AI coding CLI
ccwhat export --list      # list recorded sessions
ccwhat export <session>   # export a session
ccwhat import <archive> --open
```

Legacy `deep-ai-analysis` exports can still be imported.
