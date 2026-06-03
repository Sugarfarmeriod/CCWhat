"""Temporary current-session analysis helpers for the viewer API."""

from __future__ import annotations

import json
import subprocess
import time
from importlib import resources
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


def serialize_session_for_analysis(
    session: dict[str, Any],
    max_chars: int = MAX_ANALYSIS_CONTENT_CHARS,
) -> tuple[str, bool]:
    payload = {
        "sessionId": session.get("sessionId"),
        "projectDir": session.get("projectDir"),
        "main": session.get("main", []),
        "subagents": session.get("subagents", []),
    }
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
# Default is "claude -p -" (Claude Code pipe mode) so it works for regular
# open-source users.  Legacy internal users can set CCWHAT_ANALYZE_CMD="mc --code -p -".
_DEFAULT_ANALYZE_CMD = ["claude", "-p", "-"]


def _analyze_cmd(cmd: list[str] | tuple[str, ...] | None = None) -> list[str]:
    if cmd:
        return list(cmd)
    raw = _os.environ.get("CCWHAT_ANALYZE_CMD", "").strip()
    if raw:
        import shlex
        return shlex.split(raw)
    return list(_DEFAULT_ANALYZE_CMD)


def run_mc_analysis(
    prompt: str,
    timeout: int = ANALYZE_TIMEOUT_SECONDS,
    runner: Any | None = None,
    cmd: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, int]:
    cmd = _analyze_cmd(cmd)
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
