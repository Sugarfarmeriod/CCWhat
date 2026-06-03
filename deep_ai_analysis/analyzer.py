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
        resources.files("deep_ai_analysis")
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


def run_mc_analysis(
    prompt: str,
    timeout: int = ANALYZE_TIMEOUT_SECONDS,
    runner: Any | None = None,
) -> tuple[str, int]:
    started = time.monotonic()
    run = runner or subprocess.run
    try:
        result = run(
            ["mc", "--code", "-p", "-"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise AnalysisError("mc command not found. Please install mc first.", "mc_not_found") from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError(f"mc analysis timed out after {timeout} seconds.", "mc_timeout") from exc

    elapsed_ms = int((time.monotonic() - started) * 1000)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise AnalysisError(f"mc analysis failed: {detail}", "mc_failed")
    if not stdout:
        detail = stderr or "mc returned empty output"
        raise AnalysisError(f"mc analysis produced no report: {detail}", "empty_report")
    return stdout, elapsed_ms
