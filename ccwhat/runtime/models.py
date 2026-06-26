"""Data models for runtime task tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StepDiff:
    """Represents a single step's diff in the task.

    Attributes:
        step_index: Sequential step number (1-based)
        timestamp: ISO 8601 timestamp of the step
        tool_name: Name of the tool that made the change (e.g., "Write", "Edit")
        file_path: Path to the file that was changed
        diff: The unified diff content
    """

    step_index: int
    timestamp: str
    tool_name: str
    file_path: str
    diff: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_index": self.step_index,
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "file_path": self.file_path,
            "diff": self.diff,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepDiff:
        """Create from dictionary."""
        return cls(
            step_index=data["step_index"],
            timestamp=data["timestamp"],
            tool_name=data["tool_name"],
            file_path=data["file_path"],
            diff=data["diff"],
        )


@dataclass
class StepDiffBuffer:
    """Buffer for accumulating step diffs during a task.

    This class manages the collection of diffs from multiple steps
    and formats them into a single diff.patch file.
    """

    steps: list[StepDiff] = field(default_factory=list)
    _next_step_index: int = field(default=1, repr=False)

    def add_step(self, tool_name: str, file_path: str, diff: str) -> int:
        """Add a new step diff to the buffer.

        Args:
            tool_name: Name of the tool (e.g., "Write", "Edit")
            file_path: Path to the changed file
            diff: The diff content

        Returns:
            The assigned step index
        """
        step = StepDiff(
            step_index=self._next_step_index,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            tool_name=tool_name,
            file_path=file_path,
            diff=diff,
        )
        self.steps.append(step)
        step_index = self._next_step_index
        self._next_step_index += 1
        return step_index

    def format_patch(self) -> str:
        """Format all steps into a single diff.patch file content.

        Returns:
            Formatted diff.patch content with step headers
        """
        parts: list[str] = []
        for step in self.steps:
            # Add step header as comments
            header = f"""# Step {step.step_index}: {step.tool_name} {step.file_path}
# Timestamp: {step.timestamp}
"""
            parts.append(header)
            parts.append(step.diff)
            parts.append("")  # Empty line between steps
        return "\n".join(parts)

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.steps) == 0

    def clear(self) -> None:
        """Clear all steps."""
        self.steps.clear()
        self._next_step_index = 1
