from __future__ import annotations

from ccwhat.analyzers.base import AnalyzerSpec
from ccwhat.analyzers import codex as codex_parsers
from ccwhat.analyzers import opencode as opencode_parsers


_REGISTRY: dict[str, AnalyzerSpec] = {}

def _register(spec: AnalyzerSpec) -> None:
    for alias in _aliases(spec.name):
        _REGISTRY[alias] = spec


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
))
