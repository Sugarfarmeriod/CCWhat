from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from ccwhat.analyzers.base import AnalyzerSpec
from ccwhat.analyzers import codex as codex_parsers
from ccwhat.analyzers import opencode as opencode_parsers


_REGISTRY: dict[str, AnalyzerSpec] = {}
_CANDIDATES: dict[str, list[AnalyzerSpec]] = {}

def _register(spec: AnalyzerSpec) -> None:
    for alias in _aliases(spec.name):
        _REGISTRY[alias] = spec


def _register_candidate(spec: AnalyzerSpec) -> None:
    _CANDIDATES.setdefault(spec.name, []).append(spec)


def _aliases(name: str) -> list[str]:
    mapping = {
        "claude": ["claude", "claude-code", "claude_code", "claude-code-cli"],
        "opencode": ["opencode", "open-code", "open_code", "open-code-cli"],
        "codex": ["codex", "codex-cli"],
    }
    return mapping.get(name, [name])


def _normalize(name: str) -> str:
    lowered = name.strip().lower()
    for canonical, aliases_list in {
        "claude": ["claude", "claude-code", "claude_code"],
        "opencode": ["opencode", "open-code", "open_code"],
        "codex": ["codex"],
    }.items():
        if lowered in aliases_list:
            return canonical
    return lowered


def get(name: str) -> AnalyzerSpec | None:
    normalized = _normalize(name)
    return _REGISTRY.get(normalized)


def get_candidates(name: str) -> list[AnalyzerSpec]:
    """Return analyzer specs to try in order (for fallback)."""
    normalized = _normalize(name)
    return list(_CANDIDATES.get(normalized, []))


def prepare_candidate(spec: AnalyzerSpec, tmpdir: str | None = None) -> tuple[list[str], dict[str, str]]:
    """Prepare a candidate spec for execution.

    Returns (command, extra_files) where extra_files is passed to the parser.
    Handles dynamic substitutions such as ``<tmpfile>`` for last-message-file mode.
    """
    cmd = list(spec.default_command)
    extra_files: dict[str, str] = {}
    if spec.output_mode == "last_message_file":
        base = Path(tmpdir) if tmpdir else Path(tempfile.mkdtemp())
        base.mkdir(parents=True, exist_ok=True)
        tmp_path = str(base / "last_message.txt")
        cmd = [c if c != "<tmpfile>" else tmp_path for c in cmd]
        extra_files["last_message_file"] = tmp_path
    return cmd, extra_files


def list_names() -> list[str]:
    return list(_REGISTRY.keys())


# --- Register built-in analyzers ---

_register(AnalyzerSpec(
    name="claude",
    default_command=["claude", "-p", "-"],
    output_mode="stdout",
    experimental=False,
))

_register(AnalyzerSpec(
    name="opencode",
    default_command=["opencode", "run", "--format", "json"],
    output_mode="jsonl_text",
    experimental=False,
    parse_output=opencode_parsers.parse_jsonl_text,
))

_register(AnalyzerSpec(
    name="codex",
    default_command=["codex", "exec", "--json", "--ephemeral", "--ignore-user-config", "-"],
    output_mode="jsonl_text",
    experimental=True,
    parse_output=codex_parsers.parse_jsonl_text,
    timeout_seconds=300,
))

# Register codex last-message-file as a fallback candidate
_register_candidate(AnalyzerSpec(
    name="codex",
    default_command=["codex", "exec", "--output-last-message", "<tmpfile>", "--ephemeral", "--ignore-user-config", "-"],
    output_mode="last_message_file",
    experimental=True,
    parse_output=codex_parsers.parse_last_message_file,
    timeout_seconds=300,
))
