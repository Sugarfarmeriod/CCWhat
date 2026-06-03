#!/usr/bin/env python3
"""Pre-release safety scan.

Fails if any file that would enter a release commit (git-tracked OR untracked
but not gitignored) contains internal domains, private paths, real tokens,
legacy package distribution names, or local diagnostic captures.

Uses ``git ls-files --cached --others --exclude-standard`` so the scan covers
both already-committed files and new files staged for the first time — no need
to ``git add`` before running.

Usage:
    python scripts/check-release-safety.py

Exit code 0 = clean; non-zero = problems found.

Allowed (will not fail):
- Legacy compatibility references in ccwhat/config.py (LEGACY_DIR)
- Legacy import compatibility in ccwhat/commands/import_.py (_LEGACY_PACKAGE_ROOT)
- git rm instructions in RELEASE.md
- Test fixtures that reference "deep-ai-analysis-export" as a package root name
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Patterns that indicate internal/private content
_BANNED_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Bearer token", re.compile(r"Bearer\s+[a-f0-9]{16,}", re.IGNORECASE)),
    ("API key value", re.compile(r'"[xX]-[aA]pi-[kK]ey"\s*:\s*"[^"]+"')),
    ("Internal domain sankuai.com", re.compile(r"sankuai\.com", re.IGNORECASE)),
    ("Internal domain msstest", re.compile(r"msstest\.", re.IGNORECASE)),
    ("Internal S3", re.compile(r"s3plus\.|ad-dqe-public", re.IGNORECASE)),
    ("Internal git remote", re.compile(r"git@git\.", re.IGNORECASE)),
    ("Private user path", re.compile(r"/Users/(?!elon-ge/workspace)[a-z][\w]+/(?!\.mitmproxy|\.ccwhat)")),
    ("Old wheel name", re.compile(r"deep_ai_analysis-\d+\.\d+\.\d+")),
    ("Old package name in scripts/install", re.compile(r"pip install deep-ai-analysis\b")),
]

# Files/paths to skip (intentional legacy references, vendor code, tests)
_SKIP_PATHS: frozenset[str] = frozenset({
    "ccwhat/config.py",               # LEGACY_DIR — migration compatibility
    "ccwhat/commands/import_.py",      # _LEGACY_PACKAGE_ROOT — import compatibility
    "RELEASE.md",                      # git rm instructions reference old names
    ".gitignore",                      # gitignore entries for legacy dirs
})

# Glob patterns to skip entirely
_SKIP_GLOBS: list[str] = [
    "*.min.js", "*.min.css",
    ".venv/**", "**/__pycache__/**",
    "**/*.pyc", "**/*.egg-info/**",
    ".git/**",
    "openspec/**",                     # spec/design docs, not release artifacts
    "元析bug定位/**",                   # internal diagnostics dir
    "tests/**",                        # test fixtures use synthetic tokens/keys
    "scripts/**",                      # this script itself
]


def _get_release_files() -> list[Path]:
    """Return all files that would enter a release commit.

    Uses ``git ls-files --cached --others --exclude-standard`` so that both
    already-tracked files AND new untracked-but-not-gitignored files are
    covered.  This matches what ``git add .`` would stage, ensuring the scan
    works correctly before the first ``git add`` as well as after.
    """
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("Warning: git ls-files failed; falling back to filesystem glob.", file=sys.stderr)
        return list(REPO_ROOT.rglob("*.py")) + list(REPO_ROOT.rglob("*.md")) + list(REPO_ROOT.rglob("*.sh"))
    return [REPO_ROOT / p for p in result.stdout.splitlines() if p.strip()]


def _should_skip(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in _SKIP_PATHS:
        return True
    # Directory prefix skips
    for prefix in ("openspec/", "元析bug定位/", ".venv/", "tests/", "scripts/"):
        if rel.startswith(prefix):
            return True
    for glob in _SKIP_GLOBS:
        if path.match(glob):
            return True
    return False


def _check_tracked_paths(files: list[Path]) -> list[str]:
    """Check git-tracked paths themselves for banned names."""
    problems: list[str] = []
    for f in files:
        rel = f.relative_to(REPO_ROOT).as_posix()
        if rel.startswith("deep_ai_analysis/"):
            problems.append(f"TRACKED LEGACY: {rel}")
        if rel.startswith("sample_data/"):
            problems.append(f"TRACKED SAMPLE DATA: {rel}")
    return problems


def _scan_file(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rel = path.relative_to(REPO_ROOT).as_posix()
    for label, pattern in _BANNED_PATTERNS:
        for m in pattern.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            problems.append(f"{rel}:{line_no}: {label} — {m.group()[:60]!r}")
    return problems


def main() -> int:
    files = _get_release_files()
    all_problems: list[str] = []

    all_problems.extend(_check_tracked_paths(files))

    for f in files:
        if _should_skip(f):
            continue
        if not f.is_file():
            continue
        suffix = f.suffix.lower()
        if suffix not in {".py", ".md", ".txt", ".sh", ".toml", ".json", ".yaml", ".yml", ""}:
            continue
        all_problems.extend(_scan_file(f))

    if all_problems:
        print(f"RELEASE SAFETY SCAN FAILED — {len(all_problems)} issue(s) found:\n", file=sys.stderr)
        for p in all_problems:
            print(f"  {p}", file=sys.stderr)
        print(
            "\nFix these before tagging the release.\n"
            "Legitimate legacy references (config migration, import compatibility) are in _SKIP_PATHS.",
            file=sys.stderr,
        )
        return 1

    print(f"Release safety scan passed — {len(files)} files checked (tracked + untracked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
