from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class AdapterNotImplementedError(NotImplementedError):
    """Raised when a requested agent does not have a log adapter yet."""

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        super().__init__(
            f"No log adapter available for agent '{agent_name}'. "
            f"Only Claude Code is supported in this version. "
            f"Use --agent claude or --projects-dir to point to a Claude Code projects directory."
        )


class AgentAdapter(ABC):
    """Unified interface for reading coding agent session logs."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def default_projects_dir(self) -> Path:
        ...

    @abstractmethod
    def list_projects(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def list_sessions(self) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def load_session(self, session_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def raw_to_normalized_events(
        self, raw_entry: dict[str, Any], session_id: str
    ) -> list[dict[str, Any]]:
        ...
