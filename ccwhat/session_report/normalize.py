from __future__ import annotations

from typing import Any

from ccwhat.session_report.model import (
    ReportAgent,
    ReportEvent,
    ReportProjectRef,
    ReportSession,
    ReportTurn,
)


def _project_ref(session: dict[str, Any], agent_type: str) -> ReportProjectRef:
    fs_path = session.get("projectPath")
    project_dir = str(session.get("projectDir") or "").strip()
    if isinstance(fs_path, str) and fs_path.strip():
        return ReportProjectRef(display_name=project_dir or fs_path, fs_path=fs_path)
    if agent_type in {"codex", "opencode"} and project_dir:
        return ReportProjectRef(display_name=project_dir, fs_path=project_dir)
    return ReportProjectRef(display_name=project_dir or "", fs_path=None)


def _normalize_usage(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _event_from_normalized(raw_event: dict[str, Any], default_agent_id: str) -> ReportEvent:
    event_id = str(raw_event.get("id") or "")
    return ReportEvent(
        event_id=event_id,
        agent_id=str(raw_event.get("agentId") or default_agent_id),
        timestamp=raw_event.get("timestamp"),
        role=raw_event.get("role"),
        kind=str(raw_event.get("kind") or "unknown"),
        content=raw_event.get("content"),
        summary=str(raw_event.get("summary") or ""),
        tool_name=raw_event.get("toolName"),
        tool_call_id=raw_event.get("toolCallId"),
        parent_event_id=raw_event.get("parentId"),
        usage=_normalize_usage(raw_event.get("usage")),
        raw=raw_event.get("raw"),
    )


def _turn_from_normalized(raw_turn: dict[str, Any], default_agent_id: str) -> ReportTurn:
    raw_events = raw_turn.get("events") if isinstance(raw_turn.get("events"), list) else []
    return ReportTurn(
        turn_id=str(raw_turn.get("id") or ""),
        agent_id=str(raw_turn.get("agentId") or default_agent_id),
        started_at=raw_turn.get("startedAt"),
        ended_at=raw_turn.get("endedAt"),
        user_summary=str(raw_turn.get("userSummary") or ""),
        assistant_summary=str(raw_turn.get("assistantSummary") or ""),
        event_ids=[str(event.get("id") or "") for event in raw_events if isinstance(event, dict)],
        usage=_normalize_usage(raw_turn.get("usage")),
    )


def _normalize_claude_agents(session: dict[str, Any], primary_agent_type: str) -> list[ReportAgent]:
    agents = [
        ReportAgent(
            agent_id="main",
            agent_type=primary_agent_type,
            role="primary",
            label="main-session",
        )
    ]
    subagents = session.get("subagents") if isinstance(session.get("subagents"), list) else []
    for subagent in subagents:
        if not isinstance(subagent, dict):
            continue
        meta = subagent.get("meta") if isinstance(subagent.get("meta"), dict) else {}
        agent_id = str(subagent.get("agentId") or "unknown")
        agents.append(
            ReportAgent(
                agent_id=agent_id,
                agent_type=str(meta.get("agentType") or primary_agent_type),
                role="delegated",
                label=str(meta.get("description") or agent_id),
                parent_agent_id="main",
                metadata=meta,
            )
        )
    return agents


def _normalize_claude_events(session: dict[str, Any]) -> list[ReportEvent]:
    events: list[ReportEvent] = []
    main_entries = session.get("main") if isinstance(session.get("main"), list) else []
    for idx, entry in enumerate(main_entries, 1):
        if not isinstance(entry, dict):
            continue
        events.append(
            ReportEvent(
                event_id=f"main:{idx}",
                agent_id="main",
                timestamp=entry.get("timestamp"),
                role=entry.get("type"),
                kind="raw_entry",
                content=entry,
                summary=str(entry.get("type") or "entry"),
                raw=entry,
            )
        )
    subagents = session.get("subagents") if isinstance(session.get("subagents"), list) else []
    for subagent in subagents:
        if not isinstance(subagent, dict):
            continue
        agent_id = str(subagent.get("agentId") or "unknown")
        entries = subagent.get("entries") if isinstance(subagent.get("entries"), list) else []
        for idx, entry in enumerate(entries, 1):
            if not isinstance(entry, dict):
                continue
            events.append(
                ReportEvent(
                    event_id=f"{agent_id}:{idx}",
                    agent_id=agent_id,
                    timestamp=entry.get("timestamp"),
                    role=entry.get("type"),
                    kind="raw_entry",
                    content=entry,
                    summary=str(entry.get("type") or "entry"),
                    raw=entry,
                )
            )
    events.sort(key=lambda event: (event.timestamp or "", event.event_id))
    return events


def _normalize_claude_turns(session: dict[str, Any]) -> list[ReportTurn]:
    turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    return [_turn_from_normalized(turn, "main") for turn in turns if isinstance(turn, dict)]


def _normalize_generic_agents(session: dict[str, Any], primary_agent_type: str) -> list[ReportAgent]:
    label = str(session.get("agent") or primary_agent_type or "agent")
    return [
        ReportAgent(
            agent_id="main",
            agent_type=primary_agent_type,
            role="primary",
            label=label,
            metadata=session.get("_metadata") if isinstance(session.get("_metadata"), dict) else {},
        )
    ]


def _normalize_generic_events(session: dict[str, Any]) -> list[ReportEvent]:
    raw_events = session.get("events") if isinstance(session.get("events"), list) else []
    events = [_event_from_normalized(event, "main") for event in raw_events if isinstance(event, dict)]
    events.sort(key=lambda event: (event.timestamp or "", event.event_id))
    return events


def _derive_turns_from_events(events: list[ReportEvent], default_agent_id: str) -> list[ReportTurn]:
    turns: list[ReportTurn] = []
    current_events: list[ReportEvent] = []
    turn_start: str | None = None
    turn_index = 0

    def flush_turn() -> None:
        nonlocal current_events, turn_start, turn_index
        if not current_events:
            return
        turn_index += 1
        user_summary = ""
        assistant_summary = ""
        for event in current_events:
            if event.role == "user" and event.kind == "message" and not user_summary:
                user_summary = event.summary
            elif event.role == "assistant" and event.kind == "message":
                assistant_summary = event.summary
        turns.append(
            ReportTurn(
                turn_id=f"derived-turn:{turn_index}",
                agent_id=current_events[0].agent_id or default_agent_id,
                started_at=turn_start,
                ended_at=current_events[-1].timestamp,
                user_summary=user_summary,
                assistant_summary=assistant_summary,
                event_ids=[event.event_id for event in current_events],
                usage={},
            )
        )
        current_events = []
        turn_start = None

    for event in events:
        if event.role == "user" and event.kind == "message":
            flush_turn()
            turn_start = event.timestamp
            current_events.append(event)
            continue
        if not current_events:
            turn_start = event.timestamp
        current_events.append(event)

    flush_turn()
    return turns


def _normalize_generic_turns(session: dict[str, Any]) -> list[ReportTurn]:
    raw_turns = session.get("turns") if isinstance(session.get("turns"), list) else []
    turns = [_turn_from_normalized(turn, "main") for turn in raw_turns if isinstance(turn, dict)]
    if turns:
        return turns
    events = _normalize_generic_events(session)
    return _derive_turns_from_events(events, "main")


_VALID_REPORT_AGENTS = frozenset({"claude", "codex", "opencode"})


def _canonical_report_agent(session: dict[str, Any]) -> str:
    """Return a supported report agent type, filtering out internal agent names like 'build'."""
    raw = str(session.get("agent") or "claude").strip().lower()
    if raw in _VALID_REPORT_AGENTS:
        return raw
    meta = session.get("_metadata")
    if isinstance(meta, dict):
        source = str(meta.get("opencodeAgent") or meta.get("sourceAgent") or "").strip().lower()
        if source in _VALID_REPORT_AGENTS:
            return source
        protocol = str(meta.get("protocolAgent") or "").strip().lower()
        if protocol in _VALID_REPORT_AGENTS:
            return protocol
    return "claude"


def normalize_session_for_report(session: dict[str, Any]) -> ReportSession:
    agent_type = _canonical_report_agent(session)
    project = _project_ref(session, agent_type)
    if agent_type == "claude":
        agents = _normalize_claude_agents(session, agent_type)
        events = _normalize_claude_events(session)
        turns = _normalize_claude_turns(session)
    else:
        agents = _normalize_generic_agents(session, agent_type)
        events = _normalize_generic_events(session)
        turns = _normalize_generic_turns(session)
    return ReportSession(
        session_id=str(session.get("sessionId") or ""),
        project=project,
        primary_agent_id=agents[0].agent_id if agents else "main",
        primary_agent_type=agent_type,
        agents=agents,
        events=events,
        turns=turns,
        usage=_normalize_usage(session.get("usage")),
        metadata=session.get("_metadata") if isinstance(session.get("_metadata"), dict) else {},
    )
