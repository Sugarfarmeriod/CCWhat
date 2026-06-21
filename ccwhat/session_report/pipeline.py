"""Pipeline orchestration for Agent Session HTML reports (yuanxi and generic modes)."""

from __future__ import annotations

import html
import json
import time
from importlib import resources
from typing import Any

from ccwhat.analyzer import AnalysisError, run_mc_analysis
from ccwhat.session_report.core import build_report_data, fmt_duration, render_html_report
from ccwhat.session_report.normalize import normalize_session_for_report


MAX_EXPERIMENTAL_ANALYZER_CONTEXT_CHARS = 24_000


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


def _clip_context_for_analyzer(context: str, analyzer_agent: str | None) -> str:
    if (analyzer_agent or "").strip().lower() != "codex":
        return context
    if len(context) <= MAX_EXPERIMENTAL_ANALYZER_CONTEXT_CHARS:
        return context
    return (
        context[:MAX_EXPERIMENTAL_ANALYZER_CONTEXT_CHARS]
        + "\n\n[上下文已为 Codex experimental analyzer 截断；HTML 报告仍使用完整本地结构化数据]\n"
    )


def _fallback_diagnosis_markdown(data: Any, exc: AnalysisError) -> str:
    findings = data.findings or []
    lines = [
        "## 本地结构化诊断\n\n",
        f"> Analyzer 未完成：`{exc.code}`。以下内容来自本地日志结构化分析，不依赖大模型输出。\n\n",
        "### 关键指标\n\n",
        f"- 阶段数：{data.summary.get('phaseCount', 0)}\n",
        f"- 工具调用：{data.summary.get('toolEventCount', 0)}\n",
        f"- Agent 数：{data.summary.get('agentCount', 0)}\n",
        f"- 总耗时：{fmt_duration(data.summary.get('totalWallMin', 0))}\n",
        f"- 工具执行：{fmt_duration(data.summary.get('totalToolMin', 0))}\n",
        f"- LLM 思考：{fmt_duration(data.summary.get('totalThinkMin', 0))}\n\n",
        "### 规则发现\n\n",
    ]
    if findings:
        for finding in findings[:8]:
            lines.append(f"- [{finding.get('level')}] {finding.get('title')}：{finding.get('detail')}\n")
    else:
        lines.append("- 本地规则未发现明显异常。\n")
    return "".join(lines)


def _fallback_generic_markdown(data: Any, exc: AnalysisError) -> str:
    top_tools = sorted(
        data.tool_events,
        key=lambda event: (int(event.get("duration_ms") or 0), event.get("tool_name") or ""),
        reverse=True,
    )[:8]
    lines = [
        "# Agent 交互分析报告\n\n",
        f"> Analyzer 未完成：`{exc.code}`。以下报告来自本地日志结构化分析，用于保证报告页面可读可导出。\n\n",
        "## 概述\n\n",
        f"- Session：`{data.session_id}`\n",
        f"- Project：`{data.project_dir}`\n",
        f"- 阶段数：{data.summary.get('phaseCount', 0)}\n",
        f"- 工具调用：{data.summary.get('toolEventCount', 0)}\n",
        f"- Agent 数：{data.summary.get('agentCount', 0)}\n\n",
        "## 核心编排流程\n\n",
        "```mermaid\n",
        "flowchart TD\n",
        '    A["读取本地 Agent Session"] --> B["归一化事件与工具调用"]\n',
        '    B --> C["计算阶段耗时与工具统计"]\n',
        '    C --> D["生成本地 fallback 报告"]\n',
        "```\n\n",
        "## 阶段摘要\n\n",
    ]
    for phase in data.phases[:10]:
        lines.append(
            f"- {phase.get('name')}：总耗时 {fmt_duration(phase.get('wall_clock_min', 0))}，"
            f"工具 {fmt_duration(phase.get('tool_exec_min', 0))}，"
            f"LLM {fmt_duration(phase.get('llm_think_min', 0))}，"
            f"等待 {fmt_duration(phase.get('human_idle_min', 0))}，"
            f"工具数 {phase.get('tool_count', 0)}。\n"
        )
    if not data.phases:
        lines.append("- 本地日志缺少可用于推断阶段的时间戳。\n")
    lines.extend(["\n## 工具与能力清单\n\n"])
    if top_tools:
        for event in top_tools:
            lines.append(
                f"- {event.get('tool_name') or 'unknown'}："
                f"{fmt_duration(round((event.get('duration_ms') or 0) / 60000, 1))}，"
                f"agent={event.get('agent_id')}，`{event.get('input_summary', '')}`\n"
            )
    else:
        lines.append("- 未识别到工具调用事件。\n")
    lines.extend(["\n## 风险与建议\n\n"])
    if data.findings:
        for finding in data.findings[:8]:
            lines.append(f"- [{finding.get('level')}] {finding.get('title')}：{finding.get('detail')}\n")
    else:
        lines.append("- 暂未发现明显结构性风险；建议结合原始日志继续检查关键轮次。\n")
    return "".join(lines)


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
        prompt_context = _clip_context_for_analyzer(
            data.diagnosis_context,
            analyzer_agent or report_session.primary_agent_type,
        )
        try:
            diagnosis, llm_elapsed_ms = run_mc_analysis(
                _diagnosis_prompt(prompt_context, custom_prompt),
                cmd=analyzer_cmd,
                agent=analyzer_agent,
                default_agent=report_session.primary_agent_type,
                timeout=analyzer_timeout,
            )
            data.diagnosis_markdown = diagnosis
            diagnosis_status = {"available": True, "mode": "mc", "elapsedMs": llm_elapsed_ms}
        except AnalysisError as exc:
            diagnosis_status = {"available": False, "mode": "fallback", "code": exc.code, "message": exc.message}
            data.diagnosis_markdown = _fallback_diagnosis_markdown(data, exc)
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
        prompt_context = _clip_context_for_analyzer(
            data.diagnosis_context,
            analyzer_agent or report_session.primary_agent_type,
        )
        try:
            report_markdown, llm_elapsed_ms = run_mc_analysis(
                _generic_prompt(prompt_context, custom_prompt),
                cmd=analyzer_cmd,
                agent=analyzer_agent,
                default_agent=report_session.primary_agent_type,
                timeout=analyzer_timeout,
            )
            llm_status = {"available": True, "mode": "mc", "elapsedMs": llm_elapsed_ms}
        except AnalysisError as exc:
            llm_status = {"available": False, "mode": "fallback", "code": exc.code, "message": exc.message}
            report_markdown = _fallback_generic_markdown(data, exc)

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
