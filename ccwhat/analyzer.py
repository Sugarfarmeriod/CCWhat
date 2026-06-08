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

from ccwhat.analyzers.registry import get as _get_analyzer_spec, list_names as _list_analyzer_names

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


def _normalize_analyzer_agent(agent: str | None) -> str:
    from ccwhat.analyzers.registry import _normalize
    return _normalize(agent or "claude")


def _supported_analyzer(agent: str | None) -> bool:
    spec = _get_analyzer_spec(_normalize_analyzer_agent(agent))
    return spec is not None


def _default_analyze_cmd(agent: str | None = None) -> list[str]:
    normalized = _normalize_analyzer_agent(agent)
    spec = _get_analyzer_spec(normalized)
    if spec is None:
        raise AnalysisError(
            f"Analyzer protocol is not supported for agent '{normalized}'. "
            f"Supported agents: {', '.join(_list_analyzer_names())}",
            "analyzer_not_supported",
        )
    return list(spec.default_command)


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


def _analyze_spec(
    cmd: list[str] | tuple[str, ...] | None = None,
    agent: str | None = None,
) -> tuple[Any, list[str]]:
    """Return (spec_or_None, resolved_command) for the given config."""
    normalized = _normalize_analyzer_agent(agent)
    env_cmd = _os.environ.get("CCWHAT_ANALYZE_CMD", "").strip()
    # Only use the analyzer spec when neither explicit cmd nor env override is provided
    spec = _get_analyzer_spec(normalized) if (not cmd and not env_cmd) else None
    resolved_cmd = _analyze_cmd(cmd, agent=agent)
    return spec, resolved_cmd


def _resolve_analyzer_agent(
    agent: str | None = None,
) -> str:
    """Resolve the analyzer agent name from explicit param, env var, or default."""
    if agent:
        return _normalize_analyzer_agent(agent)
    env_agent = _os.environ.get("CCWHAT_ANALYZE_AGENT", "").strip()
    if env_agent:
        return _normalize_analyzer_agent(env_agent)
    return "claude"


def _resolve_analyzer_timeout(timeout: int | None = None) -> int:
    """Resolve timeout from explicit param, env var, or default."""
    if timeout is not None and timeout > 0:
        return timeout
    env_timeout = _os.environ.get("CCWHAT_ANALYZE_TIMEOUT", "").strip()
    if env_timeout:
        try:
            parsed = int(env_timeout)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return ANALYZE_TIMEOUT_SECONDS


def run_mc_analysis(
    prompt: str,
    timeout: int | None = None,
    runner: Any | None = None,
    cmd: list[str] | tuple[str, ...] | None = None,
    allowed_dirs: list[str] | None = None,
    agent: str | None = None,
) -> tuple[str, int]:
    normalized_agent = _resolve_analyzer_agent(agent)
    effective_timeout = _resolve_analyzer_timeout(timeout)
    spec, resolved_cmd = _analyze_spec(cmd, agent=normalized_agent)
    env_cmd = _os.environ.get("CCWHAT_ANALYZE_CMD", "").strip()

    # If cmd is provided explicitly or via env, use it regardless of spec
    has_cmd_source = bool(cmd) or bool(env_cmd)
    if spec is None and not has_cmd_source:
        raise AnalysisError(
            f"Analyzer protocol is not supported for agent '{normalized_agent}'. "
            f"Supported agents: {', '.join(_list_analyzer_names())}",
            "analyzer_not_supported",
        )

    started = time.monotonic()
    run = runner or subprocess.run
    try:
        result = run(
            resolved_cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=effective_timeout,
        )
    except FileNotFoundError as exc:
        raise AnalysisError(
            f"Analyzer command not found: {resolved_cmd[0]!r}.\n"
            "Set CCWHAT_ANALYZE_CMD to your AI CLI command, e.g.:\n"
            "  export CCWHAT_ANALYZE_CMD='claude -p -'",
            "analyzer_not_found",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError(f"Analysis timed out after {effective_timeout} seconds.", "analyzer_timeout") from exc

    elapsed_ms = int((time.monotonic() - started) * 1000)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise AnalysisError(f"Analysis failed: {detail}", "analyzer_failed")
    if not stdout:
        detail = stderr or f"{resolved_cmd[0]} returned empty output"
        raise AnalysisError(f"Analysis produced no report: {detail}", "empty_report")

    # Apply output parser for non-stdout output modes (e.g. JSONL text extraction)
    # stdout mode returns raw output unchanged for backward compatibility.
    if spec and spec.output_mode != "stdout" and spec.parse_output:
        try:
            parsed = spec.parse_output(stdout, stderr)
            if not parsed.strip():
                if not stdout.strip():
                    detail = stderr or f"{resolved_cmd[0]} returned empty output"
                    raise AnalysisError(
                        f"Analysis produced no report: {detail}",
                        "empty_report",
                    )
                raise AnalysisError(
                    "Analyzer output parser produced empty report. "
                    "The command may have returned an unexpected format.",
                    "analyzer_output_parse_error",
                )
            return parsed, elapsed_ms
        except AnalysisError:
            raise
        except Exception as exc:
            raise AnalysisError(
                f"Failed to parse analyzer output: {exc}",
                "analyzer_output_parse_error",
            ) from exc

    return stdout, elapsed_ms
