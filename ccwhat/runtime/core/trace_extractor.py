"""Extract Agent behavior trace from Claude session logs for a runtime task window."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ccwhat.task_dataset.change_evidence import extract_change_evidence
from ccwhat.task_segments.evidence import extract_evidence
from ccwhat.task_segments.events import normalize_main_entries
from ccwhat.task_segments.models import NormalizedEvent


_CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def extract_task_trace(
    workspace: str,
    started_at: str,
    finished_at: str,
    agent: str = "claude",
    projects_dir: Path | None = None,
) -> dict[str, Any]:
    """Extract Agent behavior trace from session logs for the given task time window.

    Returns a task_trace dict aligned with Dataset v1 trace structure.
    The dict always contains an extraction_status field indicating the result:
    - "ok": Normal extraction
    - "unsupported_agent": Agent is not claude
    - "invalid_time_bounds": Failed to parse time window
    - "log_not_found": Session log not found
    - "no_events": No events in time window
    """
    if agent != "claude":
        return _empty_trace(
            agent=agent,
            workspace=workspace,
            started_at=started_at,
            finished_at=finished_at,
            status="unsupported_agent",
            reason=f"Agent '{agent}' is not supported for trace extraction",
        )

    pd = projects_dir or _CLAUDE_PROJECTS_DIR
    lower, upper = _time_bounds(started_at, finished_at)
    if lower is None or upper is None:
        return _empty_trace(
            agent=agent,
            workspace=workspace,
            started_at=started_at,
            finished_at=finished_at,
            status="invalid_time_bounds",
            reason="Failed to parse started_at or finished_at timestamps",
        )

    project_dir = _project_dir_for_workspace(pd, workspace)
    if project_dir is None:
        return _empty_trace(
            agent=agent,
            workspace=workspace,
            started_at=started_at,
            finished_at=finished_at,
            status="log_not_found",
            reason=f"No session log found for workspace: {workspace}",
        )

    events = _collect_events(project_dir, lower, upper)
    if not events:
        return _empty_trace(
            agent=agent,
            workspace=workspace,
            started_at=started_at,
            finished_at=finished_at,
            status="no_events",
            reason=None,
        )

    evidence = extract_evidence(events, repo_root=workspace)
    changes, patches = extract_change_evidence(events, agent=agent)

    first_user_message = _first_user_message(events)

    return {
        "agent": agent,
        "extraction_status": "ok",
        "extraction_status_reason": None,
        "time_window": {"started_at": started_at, "finished_at": finished_at},
        "events": [_event_to_dict(e) for e in events],
        "commands": list(evidence.commands),
        "test_commands": list(evidence.test_commands),
        "files": {
            "read": list(evidence.files_read),
            "changed": list(evidence.files_changed),
        },
        "changes": changes,
        "patches": patches,
        "errors": list(evidence.errors),
        "final_claim": evidence.final_claims[0] if evidence.final_claims else None,
        "first_user_message": first_user_message,
        "repo_state": {
            "cwd": workspace,
            "base_commit": None,
            "head_commit": None,
        },
    }


def _empty_trace(
    agent: str,
    workspace: str,
    started_at: str,
    finished_at: str,
    status: str,
    reason: str | None,
) -> dict[str, Any]:
    """Return an empty trace structure for failed extraction."""
    return {
        "agent": agent,
        "extraction_status": status,
        "extraction_status_reason": reason,
        "time_window": {"started_at": started_at, "finished_at": finished_at},
        "events": [],
        "commands": [],
        "test_commands": [],
        "files": {"read": [], "changed": []},
        "changes": [],
        "patches": [],
        "errors": [],
        "final_claim": None,
        "first_user_message": None,
        "repo_state": {"cwd": None, "base_commit": None, "head_commit": None},
    }


def find_session_log_paths(workspace: str, projects_dir: Path | None = None) -> list[Path]:
    """Return all JSONL session log paths for the given workspace."""
    pd = projects_dir or _CLAUDE_PROJECTS_DIR
    project_dir = _project_dir_for_workspace(pd, workspace)
    if project_dir is None:
        return []
    return sorted(project_dir.glob("*.jsonl"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _project_dir_for_workspace(projects_dir: Path, workspace: str) -> Path | None:
    """Find the Claude project directory corresponding to the workspace path."""
    if not projects_dir.is_dir():
        return None
    encoded = workspace.replace("/", "-")
    candidate = projects_dir / encoded
    if candidate.is_dir():
        return candidate
    # Fallback: scan all project dirs for a name-match suffix
    workspace_stem = Path(workspace).name
    for d in projects_dir.iterdir():
        if d.is_dir() and d.name.endswith(f"-{workspace_stem}"):
            return d
    return None


def _time_bounds(
    started_at: str,
    finished_at: str,
    buffer_seconds: int = 1,
) -> tuple[datetime | None, datetime | None]:
    try:
        lower = _parse_ts(started_at) - timedelta(seconds=buffer_seconds)
        upper = _parse_ts(finished_at) + timedelta(seconds=buffer_seconds)
        return lower, upper
    except (ValueError, TypeError):
        return None, None


def _parse_ts(ts: str) -> datetime:
    ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)


def _collect_events(
    project_dir: Path,
    lower: datetime,
    upper: datetime,
) -> list[NormalizedEvent]:
    """Read JSONL session logs and return normalized events within the time window."""

    all_events: list[NormalizedEvent] = []
    for jsonl_path in sorted(project_dir.glob("*.jsonl")):
        first_ts, last_ts = _session_timestamps(jsonl_path)
        if not _ranges_overlap(first_ts, last_ts, lower, upper):
            continue
        entries = _read_jsonl(jsonl_path)
        if not entries:
            continue
        session_id = jsonl_path.stem
        normalized = normalize_main_entries(entries, session_id)
        for event in normalized:
            if _event_in_window(event, lower, upper):
                all_events.append(event)

    return all_events


def _session_timestamps(jsonl_path: Path) -> tuple[datetime | None, datetime | None]:
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    try:
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("timestamp")
                    if ts_str:
                        ts = _parse_ts(ts_str)
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts
                except (json.JSONDecodeError, ValueError):
                    pass
    except OSError:
        pass
    return first_ts, last_ts


def _ranges_overlap(
    first: datetime | None,
    last: datetime | None,
    lower: datetime,
    upper: datetime,
) -> bool:
    if first is None or last is None:
        return True  # unknown range — include as candidate
    return first <= upper and last >= lower


def _event_in_window(event: NormalizedEvent, lower: datetime, upper: datetime) -> bool:
    ts_str = getattr(event, "timestamp", None)
    if not ts_str:
        return False
    try:
        ts = _parse_ts(ts_str)
        return lower <= ts <= upper
    except (ValueError, TypeError):
        return False


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict):
                        entries.append(entry)
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return entries


def _first_user_message(events: list[NormalizedEvent]) -> str | None:
    for event in events:
        if event.event_type == "user_message" and event.text and event.text.strip():
            return event.text.strip()
    return None


def _event_to_dict(event: NormalizedEvent) -> dict[str, Any]:
    from dataclasses import asdict
    return asdict(event)
