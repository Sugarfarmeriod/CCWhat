"""Core logic for generic Agent Session reports."""

from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import resources
from typing import Any

from ccwhat.session_report.model import ReportEvent, ReportSession
from ccwhat.session_report.normalize import normalize_session_for_report


IDLE_THRESHOLD_MS = 10 * 60 * 1000
MAX_CONTEXT_CHARS = 60_000
MAX_DETAIL_EVENTS = 300


@dataclass
class ReportStats:
    mode: str
    rawChars: int
    compressedChars: int
    events: int
    truncatedEvents: int
    omittedEvents: int
    mainEntries: int
    subagentEntries: int
    subagents: int

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


@dataclass
class ReportData:
    session_id: str
    project_dir: str
    phases: list[dict[str, Any]]
    tool_events: list[dict[str, Any]]
    agent_summaries: list[dict[str, Any]]
    message_signals: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    summary: dict[str, Any]
    diagnosis_context: str
    compression: ReportStats
    diagnosis_markdown: str = ""
    diagnosis_status: dict[str, Any] = field(default_factory=dict)


def parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 10_000_000_000:
            number = number / 1000
        try:
            return datetime.fromtimestamp(number, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return parse_ts(int(stripped))
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def diff_ms(start: datetime | None, end: datetime | None) -> int | None:
    if not start or not end:
        return None
    return max(0, int((end - start).total_seconds() * 1000))


def ms_to_min(value: int | None) -> float:
    return round((value or 0) / 60_000, 1)


def fmt_duration(minutes: float | int | None) -> str:
    total_sec = round(float(minutes or 0) * 60)
    if total_sec < 60:
        return f"{total_sec}s"
    total_min = total_sec // 60
    sec = total_sec % 60
    if total_min < 60:
        return f"{total_min}m {sec}s" if sec else f"{total_min}m"
    hours = total_min // 60
    mins = total_min % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def content_blocks(entry: dict[str, Any]) -> list[Any]:
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else entry.get("content")
    if isinstance(content, list):
        return content
    if content in (None, ""):
        return []
    return [{"type": "text", "text": content}]


def block_text(block: Any) -> str:
    if isinstance(block, str):
        return block
    if isinstance(block, dict):
        if block.get("type") == "text":
            return str(block.get("text", ""))
        return json.dumps(block, ensure_ascii=False)
    return str(block)


def compact_text(value: Any, limit: int = 500) -> tuple[str, bool]:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text, False
    head = text[: max(80, limit - 80)].rstrip()
    return f"{head} ... [truncated {len(text)} chars]", True


def summarize_input(tool_name: str, inp: Any) -> tuple[str, bool]:
    data = inp if isinstance(inp, dict) else {}
    if tool_name == "Bash":
        return compact_text(data.get("command", ""), 500)
    if tool_name == "Agent":
        desc = data.get("description", "")
        kind = data.get("subagent_type") or "general-purpose"
        bg = " [bg]" if data.get("run_in_background") else ""
        return compact_text(f"[{kind}]{bg} {desc}", 500)
    if tool_name == "Skill":
        return compact_text(f"{data.get('skill', '')} {data.get('args', '')}", 500)
    return compact_text(inp, 500)


def signal_from_text(text: str) -> list[str]:
    lowered = text.lower()
    signals: list[str] = []
    if any(word in lowered for word in ("error", "failed", "traceback", "timeout", "失败", "报错")):
        signals.append("error_or_retry")
    if any(word in lowered for word in ("passed", "valid", "validate", "unittest", "测试通过", "成功")):
        signals.append("validation_or_test")
    if any(word in lowered for word in ("todo", "task", "计划", "完成", "- [x]", "- [ ]")):
        signals.append("task_tracking")
    if any(word in lowered for word in ("需求", "目标", "改成", "重新", "不要", "需要")):
        signals.append("goal_or_requirement")
    return signals


def report_event_text(event: ReportEvent) -> str:
    if event.kind == "raw_entry" and isinstance(event.content, dict):
        parts = [block_text(block) for block in content_blocks(event.content)]
        if parts:
            return "\n".join(parts)
    if isinstance(event.content, str):
        return event.content
    if event.content in (None, ""):
        return event.summary
    return json.dumps(event.content, ensure_ascii=False)


def report_event_blocks(event: ReportEvent) -> list[Any]:
    if event.kind == "raw_entry" and isinstance(event.content, dict):
        return content_blocks(event.content)
    if event.content in (None, ""):
        return []
    if isinstance(event.content, list):
        return event.content
    return [{"type": "text", "text": report_event_text(event)}]


def report_event_role(event: ReportEvent) -> str | None:
    if event.kind == "raw_entry" and isinstance(event.content, dict):
        raw_type = event.content.get("type")
        if isinstance(raw_type, str):
            return raw_type
    return event.role


def _report_session_from_input(session: dict[str, Any] | ReportSession) -> ReportSession:
    if isinstance(session, ReportSession):
        return session
    return normalize_session_for_report(session)


def _project_name(session: ReportSession) -> str:
    return session.project_display or session.project_path or ""


def _raw_char_size(event: ReportEvent) -> int:
    value = event.raw if event.raw is not None else event.content
    return len(json.dumps(value, ensure_ascii=False)) if value is not None else 0


def _raw_entry_counts(events: list[ReportEvent]) -> tuple[int, int]:
    main_entries = sum(1 for event in events if event.kind == "raw_entry" and event.agent_id == "main")
    subagent_entries = sum(1 for event in events if event.kind == "raw_entry" and event.agent_id != "main")
    return main_entries, subagent_entries


def _event_dt(event: dict[str, Any], key: str = "started_at") -> datetime | None:
    return parse_ts(event.get(key))


def _turn_dicts(session: ReportSession) -> list[dict[str, Any]]:
    return [
        {
            "turn_id": turn.turn_id,
            "agent_id": turn.agent_id,
            "started_at": turn.started_at,
            "ended_at": turn.ended_at,
            "user_summary": turn.user_summary,
            "assistant_summary": turn.assistant_summary,
            "event_ids": list(turn.event_ids),
            "usage": dict(turn.usage),
        }
        for turn in session.turns
    ]


def _events_by_id(session: ReportSession) -> dict[str, ReportEvent]:
    return {event.event_id: event for event in session.events}


def _turn_start_time(turn: dict[str, Any], events_by_id: dict[str, ReportEvent]) -> datetime | None:
    direct = parse_ts(turn.get("started_at"))
    if direct:
        return direct
    timestamps = [
        parse_ts(events_by_id[event_id].timestamp)
        for event_id in turn.get("event_ids", [])
        if event_id in events_by_id and parse_ts(events_by_id[event_id].timestamp)
    ]
    return min(timestamps) if timestamps else None


def _turn_label(turn: dict[str, Any], index: int) -> str:
    user_summary = str(turn.get("user_summary") or "").strip()
    if user_summary:
        return f"用户轮次 {index}: {compact_text(user_summary, 32)[0]}"
    assistant_summary = str(turn.get("assistant_summary") or "").strip()
    if assistant_summary:
        return f"轮次 {index}: {compact_text(assistant_summary, 32)[0]}"
    return f"用户轮次 {index}"


def _agent_wall_clock(agent_id: str, events: list[ReportEvent]) -> tuple[datetime | None, datetime | None]:
    timestamps = [parse_ts(event.timestamp) for event in events if event.agent_id == agent_id and parse_ts(event.timestamp)]
    if not timestamps:
        return None, None
    return min(timestamps), max(timestamps)


def _phase_boundaries_from_turns(session: ReportSession) -> list[dict[str, Any]]:
    boundaries: list[dict[str, Any]] = []
    events_by_id = _events_by_id(session)
    for idx, turn in enumerate(_turn_dicts(session), 1):
        started = _turn_start_time(turn, events_by_id)
        if not started:
            continue
        boundaries.append({
            "name": _turn_label(turn, idx),
            "start": started,
            "source": "turn",
            "confidence": 0.8,
        })
    if boundaries:
        return boundaries

    user_events = [
        event
        for event in session.events
        if (event.kind == "raw_entry" and report_event_role(event) == "user")
        or (event.role == "user" and event.kind == "message")
    ]
    for idx, event in enumerate(user_events, 1):
        started = parse_ts(event.timestamp)
        if not started:
            continue
        label = compact_text(report_event_text(event), 32)[0] or f"用户轮次 {idx}"
        boundaries.append({
            "name": f"用户轮次 {idx}: {label}",
            "start": started,
            "source": "user_event",
            "confidence": 0.7,
        })
    return boundaries


def extract_tool_events(session: ReportSession) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    tool_uses: dict[tuple[str, str], dict[str, Any]] = {}
    tool_results: dict[tuple[str, str], dict[str, Any]] = {}
    message_signals: list[dict[str, Any]] = []
    truncated = 0
    agent_labels = {agent.agent_id: agent.label for agent in session.agents}

    for event in session.events:
        ts = parse_ts(event.timestamp)
        text_parts: list[str] = []

        if event.kind == "raw_entry" and isinstance(event.content, dict):
            for block in report_event_blocks(event):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_id = str(block.get("id") or event.event_id)
                    tool_name = str(block.get("name") or "unknown")
                    tool_input = block.get("input", {})
                    summary, was_truncated = summarize_input(tool_name, tool_input)
                    truncated += int(was_truncated)
                    tool_uses[(event.agent_id, tool_id)] = {
                        "agent_id": event.agent_id,
                        "agent_description": agent_labels.get(event.agent_id, event.agent_id),
                        "source": "normalized",
                        "tool_use_id": tool_id,
                        "tool_name": tool_name,
                        "input": tool_input,
                        "input_summary": summary,
                        "started_at_dt": ts,
                        "started_at": iso(ts),
                    }
                    text_parts.append(summary)
                elif isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_id = str(block.get("tool_use_id") or event.event_id)
                    result_summary, was_truncated = compact_text(block.get("content", ""), 500)
                    truncated += int(was_truncated)
                    tool_results[(event.agent_id, tool_id)] = {
                        "ended_at_dt": ts,
                        "ended_at": iso(ts),
                        "is_error": bool(block.get("is_error")),
                        "content_summary": result_summary,
                    }
                    text_parts.append(result_summary)
                else:
                    text_parts.append(block_text(block))
        elif event.kind == "tool_call":
            tool_id = event.tool_call_id or event.event_id
            tool_name = event.tool_name or "unknown"
            summary, was_truncated = summarize_input(tool_name, event.content)
            truncated += int(was_truncated)
            tool_uses[(event.agent_id, tool_id)] = {
                "agent_id": event.agent_id,
                "agent_description": agent_labels.get(event.agent_id, event.agent_id),
                "source": "normalized",
                "tool_use_id": tool_id,
                "tool_name": tool_name,
                "input": event.content if isinstance(event.content, dict) else {},
                "input_summary": summary,
                "started_at_dt": ts,
                "started_at": iso(ts),
            }
            text_parts.append(summary)
        elif event.kind == "tool_result":
            tool_id = event.tool_call_id or event.event_id
            result_summary, was_truncated = compact_text(event.content, 500)
            truncated += int(was_truncated)
            tool_results[(event.agent_id, tool_id)] = {
                "ended_at_dt": ts,
                "ended_at": iso(ts),
                "is_error": any(token in report_event_text(event).lower() for token in ("error", "failed", "traceback", "timeout")),
                "content_summary": result_summary,
            }
            text_parts.append(result_summary)
        else:
            text = report_event_text(event)
            if text:
                text_parts.append(text)

        if text_parts:
            signals = signal_from_text("\n".join(text_parts))
            if signals:
                message_signals.append({
                    "source": "normalized",
                    "agent_id": event.agent_id,
                    "timestamp": iso(ts),
                    "signals": signals,
                    "summary": compact_text("\n".join(text_parts), 240)[0],
                })

    tool_events: list[dict[str, Any]] = []
    all_keys = sorted(set(tool_uses) | set(tool_results), key=lambda key: ((tool_uses.get(key) or tool_results.get(key) or {}).get("started_at") or (tool_results.get(key) or {}).get("ended_at") or ""))
    for key in all_keys:
        use = tool_uses.get(key, {})
        result = tool_results.get(key, {})
        start = use.get("started_at_dt")
        end = result.get("ended_at_dt")
        inp = use.get("input") if isinstance(use.get("input"), dict) else {}
        tool_events.append({
            "agent_id": use.get("agent_id") or key[0],
            "agent_description": use.get("agent_description") or agent_labels.get(key[0], key[0]),
            "source": use.get("source") or "normalized",
            "tool_use_id": use.get("tool_use_id") or key[1],
            "tool_name": use.get("tool_name") or "unknown",
            "input_summary": use.get("input_summary", ""),
            "started_at": use.get("started_at") or result.get("ended_at"),
            "ended_at": result.get("ended_at"),
            "duration_ms": diff_ms(start, end) or 0,
            "missing_result": key not in tool_results,
            "is_error": bool(result.get("is_error")),
            "content_summary": result.get("content_summary", ""),
            "spawned_agent_desc": inp.get("description") if (use.get("tool_name") == "Agent" and isinstance(inp, dict)) else None,
            "skill_name": inp.get("skill") if (use.get("tool_name") == "Skill" and isinstance(inp, dict)) else None,
        })

    tool_events.sort(key=lambda event: event.get("started_at") or event.get("ended_at") or "")
    return tool_events, message_signals, truncated


def session_bounds(session: ReportSession, tool_events: list[dict[str, Any]]) -> tuple[datetime | None, datetime | None]:
    timestamps: list[datetime] = []
    for event in session.events:
        ts = parse_ts(event.timestamp)
        if ts:
            timestamps.append(ts)
    for event in tool_events:
        for key in ("started_at", "ended_at"):
            ts = parse_ts(event.get(key))
            if ts:
                timestamps.append(ts)
    if not timestamps:
        return None, None
    return min(timestamps), max(timestamps)


def build_phases(session: ReportSession, tool_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    start, end = session_bounds(session, tool_events)
    if not start or not end:
        return []

    skill_events = [event for event in tool_events if event.get("tool_name") == "Skill" and _event_dt(event)]
    boundaries: list[dict[str, Any]] = []
    if skill_events:
        for idx, event in enumerate(skill_events, 1):
            started = _event_dt(event)
            if started:
                boundaries.append({
                    "name": event.get("skill_name") or f"阶段 {idx}",
                    "start": started,
                    "source": "skill",
                    "confidence": 0.9,
                })
    else:
        boundaries = _phase_boundaries_from_turns(session)

    if not boundaries:
        boundaries.append({"name": "完整 Session", "start": start, "source": "inferred", "confidence": 0.5})
    boundaries.sort(key=lambda item: item["start"])

    phases: list[dict[str, Any]] = []
    for idx, boundary in enumerate(boundaries):
        started = boundary["start"]
        phase_end = boundaries[idx + 1]["start"] if idx + 1 < len(boundaries) else end
        if phase_end < started:
            phase_end = started
        phases.append({
            "phase_id": f"phase-{idx + 1}",
            "name": boundary["name"],
            "source": boundary["source"],
            "confidence": boundary["confidence"],
            "started_at": iso(started),
            "ended_at": iso(phase_end),
            "tool_events": [],
            "message_signals": [],
        })
    assign_events_to_phases(phases, tool_events)
    compute_phase_metrics(phases)
    return phases


def phase_for_ts(phases: list[dict[str, Any]], value: Any) -> str | None:
    ts = parse_ts(value)
    if not ts:
        return None
    for phase in phases:
        started = parse_ts(phase.get("started_at"))
        ended = parse_ts(phase.get("ended_at"))
        if started and ended and started <= ts <= ended:
            return str(phase.get("phase_id"))
    return phases[-1]["phase_id"] if phases else None


def assign_events_to_phases(phases: list[dict[str, Any]], tool_events: list[dict[str, Any]]) -> None:
    by_id = {phase["phase_id"]: phase for phase in phases}
    for event in tool_events:
        phase_id = phase_for_ts(phases, event.get("started_at"))
        event["phase_id"] = phase_id
        if phase_id and phase_id in by_id:
            by_id[phase_id]["tool_events"].append(event)


def compute_phase_metrics(phases: list[dict[str, Any]]) -> None:
    for phase in phases:
        start = parse_ts(phase.get("started_at"))
        end = parse_ts(phase.get("ended_at"))
        wall_ms = diff_ms(start, end) or 0
        events = sorted(
            [event for event in phase.get("tool_events", []) if parse_ts(event.get("started_at"))],
            key=lambda event: event.get("started_at") or "",
        )
        tool_ms = sum(max(0, int(event.get("duration_ms") or 0)) for event in events)
        think_ms = 0
        idle_ms = 0
        cursor = start
        for event in events:
            started = parse_ts(event.get("started_at"))
            ended = parse_ts(event.get("ended_at")) or started
            gap = diff_ms(cursor, started) if cursor and started else 0
            if gap and gap >= IDLE_THRESHOLD_MS:
                idle_ms += gap
            elif gap:
                think_ms += gap
            if ended and (not cursor or ended > cursor):
                cursor = ended
        tail = diff_ms(cursor, end) if cursor and end else 0
        if tail and tail >= IDLE_THRESHOLD_MS:
            idle_ms += tail
        elif tail:
            think_ms += tail
        if not events and wall_ms:
            if wall_ms >= IDLE_THRESHOLD_MS:
                idle_ms = wall_ms
            else:
                think_ms = wall_ms
        phase["wall_clock_min"] = ms_to_min(wall_ms)
        phase["tool_exec_min"] = ms_to_min(tool_ms)
        phase["llm_think_min"] = ms_to_min(think_ms)
        phase["human_idle_min"] = ms_to_min(idle_ms)
        phase["tool_count"] = len(events)
        phase["agent_count"] = len({event.get("agent_id") for event in events if event.get("agent_id") and event.get("agent_id") != "main"})
        phase["dominant_tools"] = dominant_tools(events, limit=3)
        phase["events_preview"] = compact_detail_events(events)
        phase.pop("tool_events", None)


def dominant_tools(events: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for event in events:
        name = str(event.get("tool_name") or "unknown")
        row = stats.setdefault(name, {"tool_name": name, "count": 0, "duration_ms": 0, "errors": 0})
        row["count"] += 1
        row["duration_ms"] += int(event.get("duration_ms") or 0)
        row["errors"] += int(bool(event.get("is_error")))
    rows = sorted(stats.values(), key=lambda row: (row["duration_ms"], row["count"]), reverse=True)
    for row in rows:
        row["duration_min"] = ms_to_min(row["duration_ms"])
    return rows[:limit]


def compact_detail_events(events: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    ranked = sorted(events, key=lambda event: (bool(event.get("is_error")), int(event.get("duration_ms") or 0)), reverse=True)
    result = []
    for event in ranked[:limit]:
        result.append({
            "tool_name": event.get("tool_name"),
            "agent_id": event.get("agent_id"),
            "started_at": event.get("started_at"),
            "duration_ms": event.get("duration_ms"),
            "duration_s": round((event.get("duration_ms") or 0) / 1000, 1),
            "is_error": bool(event.get("is_error")),
            "missing_result": bool(event.get("missing_result")),
            "input_summary": event.get("input_summary", ""),
        })
    return result


def build_agent_summaries(session: ReportSession, tool_events: list[dict[str, Any]], phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for agent in session.agents:
        start, end = _agent_wall_clock(agent.agent_id, session.events)
        events = [event for event in tool_events if event.get("agent_id") == agent.agent_id]
        phase_id = phase_for_ts(phases, iso(start)) or "unknown"
        summaries.append({
            "agent_id": agent.agent_id,
            "description": agent.label,
            "agent_type": agent.agent_type,
            "started_at": iso(start),
            "ended_at": iso(end),
            "wall_clock_min": ms_to_min(diff_ms(start, end)),
            "tool_count": len(events),
            "phase_id": phase_id,
            "dominant_tools": dominant_tools(events, limit=3),
            "role": agent.role,
            "parent_agent_id": agent.parent_agent_id,
        })
    return summaries


def rule_findings(phases: list[dict[str, Any]], tool_events: list[dict[str, Any]], agent_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for phase in sorted(phases, key=lambda phase: (phase.get("tool_exec_min", 0) or 0) + (phase.get("llm_think_min", 0) or 0), reverse=True)[:5]:
        active = (phase.get("tool_exec_min", 0) or 0) + (phase.get("llm_think_min", 0) or 0)
        if active >= 10:
            findings.append({
                "level": "high" if active >= 30 else "medium",
                "title": f"阶段耗时较高：{phase.get('name')}",
                "detail": f"有效耗时 {fmt_duration(active)}，工具 {fmt_duration(phase.get('tool_exec_min'))}，LLM {fmt_duration(phase.get('llm_think_min'))}",
                "phase_id": phase.get("phase_id"),
            })
        if (phase.get("human_idle_min") or 0) >= 10:
            findings.append({
                "level": "medium",
                "title": f"存在长时间等待：{phase.get('name')}",
                "detail": f"人工等待 {fmt_duration(phase.get('human_idle_min'))}",
                "phase_id": phase.get("phase_id"),
            })

    errors = [event for event in tool_events if event.get("is_error")]
    if errors:
        findings.append({
            "level": "high",
            "title": "工具调用出现失败",
            "detail": f"共 {len(errors)} 次失败，主要工具：{', '.join(row['tool_name'] for row in dominant_tools(errors, 3))}",
        })
    for row in dominant_tools(tool_events, limit=8):
        if row["count"] >= 10:
            findings.append({
                "level": "medium",
                "title": f"{row['tool_name']} 高频调用",
                "detail": f"调用 {row['count']} 次，累计 {fmt_duration(row['duration_min'])}",
            })
    delegated = [agent for agent in agent_summaries if agent.get("role") == "delegated"]
    if delegated:
        findings.append({
            "level": "medium",
            "title": "存在委派 Agent 协作",
            "detail": f"共 {len(delegated)} 个 delegated agent 参与，主 Agent 之外存在分工执行痕迹",
        })
    return findings[:10]


def build_context(
    session_id: str,
    project_dir: str,
    phases: list[dict[str, Any]],
    tool_events: list[dict[str, Any]],
    agent_summaries: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    raw_chars: int,
    truncated_events: int,
) -> tuple[str, ReportStats]:
    lines = [
        "# 通用 Agent Session 诊断上下文\n\n",
        f"- Session: `{session_id}`\n",
        f"- Project: `{project_dir}`\n",
        f"- 阶段数: {len(phases)}\n",
        f"- 工具事件数: {len(tool_events)}\n",
        f"- Agent 数: {len(agent_summaries)}\n\n",
        "## 阶段耗时排行\n\n",
        "| 阶段 | 来源 | 总时间 | 工具 | LLM | 等待 | 工具数 |\n",
        "|---|---|---:|---:|---:|---:|---:|\n",
    ]
    for phase in sorted(phases, key=lambda item: item.get("wall_clock_min", 0), reverse=True)[:20]:
        lines.append(
            f"| {phase.get('name')} | {phase.get('source')} | {fmt_duration(phase.get('wall_clock_min'))} | "
            f"{fmt_duration(phase.get('tool_exec_min'))} | {fmt_duration(phase.get('llm_think_min'))} | "
            f"{fmt_duration(phase.get('human_idle_min'))} | {phase.get('tool_count', 0)} |\n"
        )
    lines.append("\n## 规则诊断\n\n")
    for finding in findings:
        lines.append(f"- [{finding.get('level')}] {finding.get('title')}: {finding.get('detail')}\n")
    lines.append("\n## 慢工具事件\n\n")
    slow = sorted(tool_events, key=lambda item: int(item.get("duration_ms") or 0), reverse=True)[:30]
    for event in slow:
        lines.append(
            f"- {event.get('tool_name')} {round((event.get('duration_ms') or 0) / 1000)}s "
            f"agent={event.get('agent_id')}: `{event.get('input_summary', '')}`\n"
        )
    lines.append("\n## Agent 摘要\n\n")
    for agent in agent_summaries[:20]:
        lines.append(
            f"- {agent.get('description')}：{fmt_duration(agent.get('wall_clock_min'))}，工具 {agent.get('tool_count')} 次，阶段 {agent.get('phase_id')}\n"
        )
    context = "".join(lines)
    omitted = 0
    if len(context) > MAX_CONTEXT_CHARS:
        omitted = len(context) - MAX_CONTEXT_CHARS
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[上下文已按预算截断]\n"
    subagents = len([agent for agent in agent_summaries if agent.get("role") == "delegated"])
    stats = ReportStats(
        mode="structured_html",
        rawChars=raw_chars,
        compressedChars=len(context),
        events=len(tool_events),
        truncatedEvents=truncated_events,
        omittedEvents=omitted,
        mainEntries=0,
        subagentEntries=0,
        subagents=subagents,
    )
    return context, stats


def build_report_data(session: dict[str, Any] | ReportSession) -> ReportData:
    report_session = _report_session_from_input(session)
    tool_events, signals, truncated = extract_tool_events(report_session)
    phases = build_phases(report_session, tool_events)
    agents = build_agent_summaries(report_session, tool_events, phases)
    findings = rule_findings(phases, tool_events, agents)
    raw_chars = sum(_raw_char_size(event) for event in report_session.events)
    context, compression = build_context(
        report_session.session_id,
        _project_name(report_session),
        phases,
        tool_events,
        agents,
        findings,
        raw_chars,
        truncated,
    )
    main_entries, subagent_entries = _raw_entry_counts(report_session.events)
    compression.mainEntries = main_entries
    compression.subagentEntries = subagent_entries
    summary = {
        "sessionId": report_session.session_id,
        "projectDir": _project_name(report_session),
        "phaseCount": len(phases),
        "toolEventCount": len(tool_events),
        "agentCount": len(agents),
        "findingCount": len(findings),
        "totalWallMin": round(sum(phase.get("wall_clock_min", 0) or 0 for phase in phases), 1),
        "totalToolMin": round(sum(phase.get("tool_exec_min", 0) or 0 for phase in phases), 1),
        "totalThinkMin": round(sum(phase.get("llm_think_min", 0) or 0 for phase in phases), 1),
        "totalIdleMin": round(sum(phase.get("human_idle_min", 0) or 0 for phase in phases), 1),
    }
    return ReportData(
        session_id=report_session.session_id,
        project_dir=_project_name(report_session),
        phases=phases,
        tool_events=tool_events,
        agent_summaries=agents,
        message_signals=signals,
        findings=findings,
        summary=summary,
        diagnosis_context=context,
        compression=compression,
    )


def render_html_report(data: ReportData) -> str:
    payload = {
        "summary": data.summary,
        "phases": data.phases,
        "toolEvents": compact_detail_events(data.tool_events, MAX_DETAIL_EVENTS),
        "agents": data.agent_summaries,
        "findings": data.findings,
        "diagnosisMarkdown": data.diagnosis_markdown,
        "diagnosisStatus": data.diagnosis_status,
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    template = resources.files("ccwhat").joinpath("assets/session-report/report_template.html").read_text(encoding="utf-8")
    return (
        template
        .replace("{{session_id}}", html.escape(data.session_id))
        .replace("{{project_dir}}", html.escape(data.project_dir))
        .replace("{{report_data_json}}", payload_json)
    )
