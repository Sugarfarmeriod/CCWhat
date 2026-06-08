"""Pipeline orchestration for Agent Session HTML reports (yuanxi and generic modes)."""

from __future__ import annotations

import hashlib
import html
import json
import time
from importlib import resources
from typing import Any

from ccwhat.analyzer import AnalysisError, run_mc_analysis
from ccwhat.session_report.core import build_report_data, render_html_report
from ccwhat.session_report.normalize import normalize_session_for_report


def _diagnosis_prompt(context: str, custom_prompt: str = "") -> str:
    template = resources.files("ccwhat").joinpath("assets/session-report/diagnosis_prompt.md").read_text(encoding="utf-8")
    result = template.replace("{{diagnosis_context}}", context)
    if custom_prompt:
        result += f"\n\n---\n\n## 用户自定义关注点\n\n{custom_prompt}"
    return result


def _generic_prompt(context: str, custom_prompt: str = "") -> str:
    template = resources.files("ccwhat").joinpath("assets/session-report/generic_prompt.md").read_text(encoding="utf-8")
    result = template.replace("{{diagnosis_context}}", context)
    if custom_prompt:
        result += f"\n\n---\n\n## 用户自定义关注点\n\n{custom_prompt}"
    return result


def _get_mermaid_script_tag() -> str:
    """Load vendor mermaid.min.js and return a <script> tag.

    Returns an empty string if the vendor file is missing, which means Mermaid
    blocks will fall back to displaying raw code in the rendered report.
    Install or copy mermaid.min.js to
    ccwhat/assets/session-report/vendor/mermaid.min.js to enable
    full Mermaid rendering.
    """
    import warnings
    try:
        js = resources.files("ccwhat").joinpath(
            "assets/session-report/vendor/mermaid.min.js"
        ).read_text(encoding="utf-8")
        return f"<script>{js}</script>"
    except (FileNotFoundError, Exception):
        warnings.warn(
            "Mermaid vendor file not found at "
            "ccwhat/assets/session-report/vendor/mermaid.min.js. "
            "Mermaid diagrams in generic reports will fall back to source code display.",
            RuntimeWarning,
            stacklevel=3,
        )
        return ""


def _render_generic_html(
    session_id: str,
    project_dir: str,
    report_markdown: str,
    custom_prompt: str = "",
    mode: str = "generic",
) -> str:
    template = resources.files("ccwhat").joinpath("assets/session-report/generic_template.html").read_text(encoding="utf-8")
    content_json = json.dumps(report_markdown, ensure_ascii=False).replace("</", "<\\/")
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    custom_note = ""
    if custom_prompt:
        preview = custom_prompt[:60] + ("…" if len(custom_prompt) > 60 else "")
        custom_note = f'<span>关注点: {html.escape(preview)}</span>'
    return (
        template
        .replace("{{session_id}}", html.escape(session_id))
        .replace("{{project_dir}}", html.escape(project_dir))
        .replace("{{generated_at}}", html.escape(generated_at))
        .replace("{{custom_prompt_note}}", custom_note)
        .replace("{{report_content_json}}", content_json)
        .replace("{{mermaid_script_tag}}", _get_mermaid_script_tag())
    )


def build_html_session_report(
    session: dict[str, Any],
    *,
    allowed_dirs: list[str] | None = None,
    enable_llm: bool = True,
    custom_prompt: str = "",
    analyzer_cmd: list[str] | tuple[str, ...] | None = None,
    analyzer_agent: str | None = None,
    analyzer_timeout: int | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    report_session = normalize_session_for_report(session)
    data = build_report_data(report_session)
    diagnosis_status: dict[str, Any] = {"available": False, "mode": "not_requested"}
    llm_elapsed_ms = 0
    if enable_llm:
        try:
            diagnosis, llm_elapsed_ms = run_mc_analysis(
                _diagnosis_prompt(data.diagnosis_context, custom_prompt),
                allowed_dirs=allowed_dirs,
                cmd=analyzer_cmd,
                agent=analyzer_agent or report_session.primary_agent_type,
                timeout=analyzer_timeout,
            )
            data.diagnosis_markdown = diagnosis
            diagnosis_status = {"available": True, "mode": "mc", "elapsedMs": llm_elapsed_ms}
        except AnalysisError as exc:
            diagnosis_status = {"available": False, "mode": "fallback", "code": exc.code, "message": exc.message}
    data.diagnosis_status = diagnosis_status
    html_content = render_html_report(data)
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return {
        "reportType": "html",
        "reportMode": "yuanxi",
        "reportHtml": html_content,
        "summary": data.summary,
        "compression": data.compression.to_dict(),
        "diagnosisStatus": diagnosis_status,
        "elapsedMs": elapsed_ms,
        "llmElapsedMs": llm_elapsed_ms,
    }


def build_generic_html_report(
    session: dict[str, Any],
    *,
    allowed_dirs: list[str] | None = None,
    enable_llm: bool = True,
    custom_prompt: str = "",
    analyzer_cmd: list[str] | tuple[str, ...] | None = None,
    analyzer_agent: str | None = None,
    analyzer_timeout: int | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    report_session = normalize_session_for_report(session)
    data = build_report_data(report_session)
    llm_elapsed_ms = 0
    report_markdown = ""
    llm_status: dict[str, Any] = {"available": False, "mode": "not_requested"}

    if enable_llm:
        try:
            report_markdown, llm_elapsed_ms = run_mc_analysis(
                _generic_prompt(data.diagnosis_context, custom_prompt),
                allowed_dirs=allowed_dirs,
                cmd=analyzer_cmd,
                agent=analyzer_agent or report_session.primary_agent_type,
                timeout=analyzer_timeout,
            )
            llm_status = {"available": True, "mode": "mc", "elapsedMs": llm_elapsed_ms}
        except AnalysisError as exc:
            llm_status = {"available": False, "mode": "fallback", "code": exc.code, "message": exc.message}
            report_markdown = f"# 报告生成失败\n\n{exc.message}"

    html_content = _render_generic_html(
        session_id=report_session.session_id,
        project_dir=report_session.project_display,
        report_markdown=report_markdown,
        custom_prompt=custom_prompt,
    )
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return {
        "reportType": "html",
        "reportMode": "generic",
        "reportHtml": html_content,
        "summary": data.summary,
        "compression": data.compression.to_dict(),
        "llmStatus": llm_status,
        "elapsedMs": elapsed_ms,
        "llmElapsedMs": llm_elapsed_ms,
    }
