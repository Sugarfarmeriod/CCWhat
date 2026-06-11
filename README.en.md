# 🔬 codelenagent（see see what）

[中文](README.md) | English

Current version: `v1.0.0` · [Changelog](CHANGELOG.md)

## Current Status

`v1.0.0` adds the Task Trace Workbench and first rule-based task segmentation. **codelenagent can now identify multiple coding tasks inside a long session while continuing to support Claude Code (VS Code), Codex, and OpenCode.** Log viewing, task segmentation, evidence navigation, analysis reports, timelines, tool timing, and agent summaries work across all three.

**Your AI being sneaky again? See see what it's actually doing.**

---

## 😤 Sound familiar?

- You tell Claude Code to go left, it goes right, and invents a third direction on its own
- You say "reference this doc", it instantly replies "done!", but never opened the file
- You ask "did you actually read it?" — it says yes with full confidence
- You dig through terminal logs, can't find any proof, and just feel gaslit

**Stop letting AI play you.**  
codelenagent is built for exactly this — **a scalpel + a microscope** that puts every move your agent makes right in front of your eyes.

---

## ❓ What is codelenagent

codelenagent (pronounced "see see what")  
It does one thing:

> **Records everything your AI does while working, then plays it back in a browser so you can watch in real time.**

- What tools it called
- Which files it read (or pretended to read)
- What commands it ran and what came back
- Whether it actually "referenced the doc" or just made stuff up

**Every move. In plain sight.**

---

## 🚀 Up in 3 seconds

Install or update:

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash
```

Run (the space matters — it's the soul of the command):

```bash
ccwhat -- claude
ccwhat -- codex
# or whatever CLI you use
ccwhat -- xx
```

Uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/PacemakerG/CCWhat/main/install.sh | bash -s -- uninstall
```

*First run walks you through picking what to record. Just follow the prompts.*

---

## 🦥 Lazy mode

Paste the install command into your Claude Code / Codex CLI / any AI shell, and say:

> "Install codelenagent for me"

It'll handle everything. You don't have to lift a finger.  
(Think of it as putting an honesty bracelet on your AI.)

---

## 📺 Live feed

After launch, a viewer tab opens automatically. Every agent action shows up in real time.

Closed the tab by accident? Reopen it:

```bash
ccwhat web
```

Or go directly to `http://127.0.0.1:7789/claude-log.html`

---

## ⚠️ Notes

- Supports macOS, Linux, and WSL. Windows native is not supported yet (working on it)
- Python 3.10+ and mitmproxy are required; the install script checks them
- HTTPS recording requires trusting the mitmproxy CA certificate (like putting a wiretap on your agent — you have to consent first)
- Authorization, cookies, API keys and other sensitive headers are automatically redacted
- Discovery mode records action metadata only, no payloads — good for a quick "is it behaving?" check

---

## 🛠️ Useful commands

```bash
ccwhat setup                   # change recording config
ccwhat web                     # reopen the viewer
ccwhat discover -- claude      # scout mode: log actions, skip payloads
ccwhat discover -- codex       # scout Codex traffic too
ccwhat run --no-web -- claude  # run quietly, no auto browser
ccwhat export --list           # list recorded sessions
ccwhat export <session>        # export a session
ccwhat import <archive> --open # load someone else's session, investigate together
```

---

## 🧬 More on the way

This project is moving fast. Feedback, issues, and PRs are all welcome.

- **Have ideas?** Open an issue — even "why doesn't this exist yet" counts
- **Can code?** Submit a PR
- **Find it interesting?** Drop a ⭐ Star and become a spiritual stakeholder
