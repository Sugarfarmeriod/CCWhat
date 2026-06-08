from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReportProjectRef:
    display_name: str
    fs_path: str | None = None


@dataclass(slots=True)
class ReportAgent:
    agent_id: str
    agent_type: str
    role: str
    label: str
    parent_agent_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReportEvent:
    event_id: str
    agent_id: str
    timestamp: str | None
    role: str | None
    kind: str
    content: Any = None
    summary: str = ""
    tool_name: str | None = None
    tool_call_id: str | None = None
    parent_event_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    raw: Any = None


@dataclass(slots=True)
class ReportTurn:
    turn_id: str
    agent_id: str
    started_at: str | None
    ended_at: str | None
    user_summary: str = ""
    assistant_summary: str = ""
    event_ids: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReportSession:
    session_id: str
    project: ReportProjectRef
    primary_agent_id: str
    primary_agent_type: str
    agents: list[ReportAgent] = field(default_factory=list)
    events: list[ReportEvent] = field(default_factory=list)
    turns: list[ReportTurn] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def project_display(self) -> str:
        return self.project.display_name

    @property
    def project_path(self) -> str | None:
        return self.project.fs_path
