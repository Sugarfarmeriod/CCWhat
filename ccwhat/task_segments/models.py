"""Task segmentation data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NormalizedEvent:
    event_id: str           # e.g. "main:42" or "agent-abc:7"
    source: str             # "main" | "subagent"
    agent_id: str           # "main" or subagent id
    turn_index: int
    event_type: str         # user_message|assistant_text|tool_call|tool_result|
                            # file_read|file_edit|command|error|todo|final_claim
    text: str
    tool_name: str | None = None
    tool_use_id: str | None = None
    files: list[str] = field(default_factory=list)
    command: str | None = None
    timestamp: str | None = None
    raw_ref: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceBundle:
    files_read: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    subagent_ids: list[str] = field(default_factory=list)
    final_claims: list[str] = field(default_factory=list)
    todos_user: list[str] = field(default_factory=list)
    todos_assistant: list[str] = field(default_factory=list)
    todos_tool: list[str] = field(default_factory=list)
    file_weights: dict[str, float] = field(default_factory=dict)

    def all_files(self) -> list[str]:
        seen: set[str] = set()
        result = []
        for f in self.files_read + self.files_changed:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result


@dataclass
class IntentResult:
    new_task_score: float = 0.0
    continuation_score: float = 0.0
    task_type: str = "unknown"
    is_veto: bool = False          # continuation veto — must not open new task
    reasons: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)


@dataclass
class BoundaryDecision:
    event_id: str
    score: float
    should_split: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class TaskSegment:
    task_id: str
    title: str
    task_type: str
    status: str                        # always "unevaluated" in v1
    start_event_id: str
    end_event_id: str | None
    boundary_reasons: list[str] = field(default_factory=list)
    evidence: EvidenceBundle = field(default_factory=EvidenceBundle)
    file_weights: dict[str, float] = field(default_factory=dict)
    is_ambiguous: bool = False
    final_claim: str | None = None
    is_open: bool = True


@dataclass
class TaskSegmentationResult:
    session_id: str
    tasks: list[TaskSegment] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    is_ambiguous: bool = False
    debug_boundaries: list[BoundaryDecision] = field(default_factory=list)
