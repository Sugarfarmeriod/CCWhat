"""Codex hook entry point for CCWhat slash commands.

Thin shim retained so ``python -m ccwhat.runtime.codex_hook`` (the command
written into installed Codex hook scripts) keeps resolving. Implementation
lives in :mod:`ccwhat.runtime.hooks.codex`.
"""

from __future__ import annotations

from ccwhat.runtime.hooks.codex import main


if __name__ == "__main__":
    raise SystemExit(main())
