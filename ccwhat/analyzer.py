"""Temporary current-session analysis helpers for the viewer API."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from importlib import resources
from pathlib import Path
from typing import Any


ANALYZE_TIMEOUT_SECONDS = 120
MAX_ANALYSIS_CONTENT_CHARS = 120_000
_PROMPT_PLACEHOLDER = "{{content}}"


class AnalysisError(Exception):
    """User-facing analysis failure."""

    def __init__(self, message: str, code: str = "analysis_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def load_analyze_prompt_template() -> str:
    return (
        resources.files("ccwhat")
        .joinpath("assets/analyze_prompt.md")
        .read_text(encoding="utf-8")
    )


def _serialize_report_session(report_session: Any) -> dict[str, Any]:
    return {
        "sessionId": report_session.session_id,
        "project": {
            "displayName": report_session.project.display_name,
            "fsPath": report_session.project.fs_path,
        },
        "primaryAgentId": report_session.primary_agent_id,
        "primaryAgentType": report_session.primary_agent_type,
        "agents": [
            {
                "agentId": agent.agent_id,
                "agentType": agent.agent_type,
                "role": agent.role,
                "label": agent.label,
                "parentAgentId": agent.parent_agent_id,
                "metadata": agent.metadata,
            }
            for agent in report_session.agents
        ],
        "turns": [
            {
                "turnId": turn.turn_id,
                "agentId": turn.agent_id,
                "startedAt": turn.started_at,
                "endedAt": turn.ended_at,
                "userSummary": turn.user_summary,
                "assistantSummary": turn.assistant_summary,
                "eventIds": turn.event_ids,
                "usage": turn.usage,
            }
            for turn in report_session.turns
        ],
        "events": [
            {
                "eventId": event.event_id,
                "agentId": event.agent_id,
                "timestamp": event.timestamp,
                "role": event.role,
                "kind": event.kind,
                "summary": event.summary,
                "toolName": event.tool_name,
                "toolCallId": event.tool_call_id,
                "parentEventId": event.parent_event_id,
                "content": event.content,
                "usage": event.usage,
            }
            for event in report_session.events
        ],
        "usage": report_session.usage,
        "metadata": report_session.metadata,
    }


def serialize_session_for_analysis(
    session: dict[str, Any],
    max_chars: int = MAX_ANALYSIS_CONTENT_CHARS,
) -> tuple[str, bool]:
    from ccwhat.session_report.normalize import normalize_session_for_report

    report_session = normalize_session_for_report(session)
    payload = _serialize_report_session(report_session)
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(content) <= max_chars:
        return content, False
    marker = (
        "\n\n[TRUNCATED] 当前 session 内容超过分析输入上限，"
        "这里只保留前部内容；报告可能遗漏后续交互。\n"
    )
    return content[:max_chars] + marker, True


def build_analysis_prompt(
    session: dict[str, Any],
    template: str | None = None,
    max_chars: int = MAX_ANALYSIS_CONTENT_CHARS,
) -> tuple[str, bool]:
    prompt_template = template if template is not None else load_analyze_prompt_template()
    content, truncated = serialize_session_for_analysis(session, max_chars=max_chars)
    if _PROMPT_PLACEHOLDER in prompt_template:
        return prompt_template.replace(_PROMPT_PLACEHOLDER, content), truncated
    return f"{prompt_template.rstrip()}\n\n{content}", truncated


import os as _os

# The analysis command can be overridden via CCWHAT_ANALYZE_CMD env var.
# Without an explicit command or env override, pick a non-interactive default
# based on the current agent so multi-agent viewers do not silently fall back
# to Claude.
_DEFAULT_ANALYZE_CMDS = {
    "claude": ["claude", "-p", "-"],
    "codex": ["codex", "exec", "-"],
}

_ANALYZER_STDIN_COMPATIBLE_AGENTS = frozenset({"claude", "codex"})

_KNOWN_BINARY_PATHS = {
    "codex": "/Applications/Codex.app/Contents/Resources/codex",
    "opencode": "/Applications/OpenCode.app/Contents/MacOS/opencode",
}


def _resolve_binary(cmd: list[str]) -> list[str]:
    if not cmd:
        return cmd
    binary = cmd[0]
    if Path(binary).is_file():
        return cmd
    resolved = shutil.which(binary)
    if resolved:
        updated = list(cmd)
        updated[0] = resolved
        return updated
    known = _KNOWN_BINARY_PATHS.get(binary)
    if known and Path(known).is_file():
        updated = list(cmd)
        updated[0] = known
        return updated
    return cmd


def _supports_stdin_analysis(agent: str | None) -> bool:
    return _normalize_analyzer_agent(agent) in _ANALYZER_STDIN_COMPATIBLE_AGENTS


def _normalize_analyzer_agent(agent: str | None) -> str:
    lowered = str(agent or "claude").strip().lower()
    if lowered in {"open-code", "open_code"}:
        return "opencode"
    if lowered in {"claude", "codex", "opencode"}:
        return lowered
    return "claude"


def _default_analyze_cmd(agent: str | None = None) -> list[str]:
    normalized = _normalize_analyzer_agent(agent)
    cmd = _DEFAULT_ANALYZE_CMDS.get(normalized)
    if cmd is None:
        raise AnalysisError(
            f"Analyzer protocol is not supported for agent '{normalized}'.",
            "analyzer_not_supported",
        )
    return list(cmd)


def _analyze_cmd(
    cmd: list[str] | tuple[str, ...] | None = None,
    agent: str | None = None,
) -> list[str]:
    if cmd:
        return _resolve_binary(list(cmd))
    raw = _os.environ.get("CCWHAT_ANALYZE_CMD", "").strip()
    if raw:
        import shlex
        return _resolve_binary(shlex.split(raw))
    return _resolve_binary(_default_analyze_cmd(agent))


def run_mc_analysis(
    prompt: str,
    timeout: int = ANALYZE_TIMEOUT_SECONDS,
    runner: Any | None = None,
    cmd: list[str] | tuple[str, ...] | None = None,
    allowed_dirs: list[str] | None = None,  # accepted for API compat; unused by configurable-cmd model
    agent: str | None = None,
) -> tuple[str, int]:
    normalized_agent = _normalize_analyzer_agent(agent)
    if cmd is None and not _supports_stdin_analysis(normalized_agent):
        raise AnalysisError(
            f"Analyzer protocol is not supported for agent '{normalized_agent}'. "
            "This agent does not support the current stdin/stdout analysis runner.",
            "analyzer_not_supported",
        )
    cmd = _analyze_cmd(cmd, agent=normalized_agent)
    started = time.monotonic()
    run = runner or subprocess.run
    try:
        result = run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise AnalysisError(
            f"Analyzer command not found: {cmd[0]!r}.\n"
            "Set CCWHAT_ANALYZE_CMD to your AI CLI command, e.g.:\n"
            "  export CCWHAT_ANALYZE_CMD='claude -p -'",
            "analyzer_not_found",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError(f"Analysis timed out after {timeout} seconds.", "analyzer_timeout") from exc

    elapsed_ms = int((time.monotonic() - started) * 1000)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise AnalysisError(f"Analysis failed: {detail}", "analyzer_failed")
    if not stdout:
        detail = stderr or f"{cmd[0]} returned empty output"
        raise AnalysisError(f"Analysis produced no report: {detail}", "empty_report")
    return stdout, elapsed_ms
