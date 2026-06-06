from __future__ import annotations

from pathlib import Path
from typing import Any

from ccwhat.adapters.base import AdapterNotImplementedError, AgentAdapter
from ccwhat.adapters.claude import ClaudeAdapter


_AGENT_ALIASES: dict[str, str] = {
    "claude": "claude",
    "claude-code": "claude",
    "codex": "codex",
    "opencode": "opencode",
    "open-code": "opencode",
    "open_code": "opencode",
}


_IMPLEMENTED_AGENTS = frozenset({"claude"})


def normalize_agent_name(name: str) -> str:
    lowered = name.strip().lower()
    return _AGENT_ALIASES.get(lowered, lowered)


def is_implemented(agent: str) -> bool:
    return agent in _IMPLEMENTED_AGENTS


def create_adapter(agent: str, projects_dir: Path | None = None) -> AgentAdapter:
    normalized = normalize_agent_name(agent)
    if not is_implemented(normalized):
        raise AdapterNotImplementedError(agent)
    if normalized == "claude":
        return ClaudeAdapter(projects_dir)
    raise AdapterNotImplementedError(agent)


def infer_agent_from_target(target_args: tuple[str, ...]) -> str:
    if not target_args:
        return "claude"
    target = target_args[0].lower()
    return normalize_agent_name(target)
