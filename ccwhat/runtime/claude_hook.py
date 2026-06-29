"""Claude Code hook entry point for CCWhat slash commands.

Thin shim retained so ``python -m ccwhat.runtime.claude_hook`` (the command
written into installed Claude hook scripts) keeps resolving. Implementation
lives in :mod:`ccwhat.runtime.hooks.claude`.
"""

from __future__ import annotations

from ccwhat.runtime.hooks.claude import main


if __name__ == "__main__":
    raise SystemExit(main())
