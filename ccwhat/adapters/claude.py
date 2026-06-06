from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ccwhat.adapters.base import AgentAdapter


def _read_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry["_fileLine"] = lineno
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def _session_timestamps(jsonl_path: Path) -> tuple[str | None, str | None]:
    first_ts: str | None = None
    last_ts: str | None = None
    try:
        with jsonl_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp")
                    if ts:
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return first_ts, last_ts


def _load_subagents(session_dir: Path) -> list[dict[str, Any]]:
    subagents_dir = session_dir / "subagents"
    if not subagents_dir.is_dir():
        return []
    subagents = []
    for jsonl_path in sorted(subagents_dir.glob("agent-*.jsonl")):
        agent_id = jsonl_path.stem[len("agent-"):]
        meta_path = subagents_dir / f"agent-{agent_id}.meta.json"
        meta: dict = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        entries = _read_jsonl(jsonl_path)
        subagents.append({
            "agentId": agent_id,
            "meta": meta,
            "entries": entries,
        })
    return subagents


def _normalize_usage(entry: dict) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    raw = entry.get("message", {}).get("usage", {})
    if not raw and "usage" in entry:
        raw = entry.get("usage", {})
    if raw:
        usage["inputTokens"] = raw.get("input_tokens") or raw.get("inputTokens")
        usage["outputTokens"] = raw.get("output_tokens") or raw.get("outputTokens")
        if "cache_read_input_tokens" in raw or "cacheReadInputTokens" in raw or "cache_read_creation_tokens" in raw or "cacheCreationTokens" in raw:
            usage["cacheReadTokens"] = raw.get("cache_read_input_tokens") or raw.get("cacheReadInputTokens")
            usage["cacheWriteTokens"] = raw.get("cache_write_input_tokens") or raw.get("cacheWriteInputTokens")
            usage["cacheCreationTokens"] = raw.get("cache_read_creation_tokens") or raw.get("cacheCreationTokens")
        reasoning = raw.get("reasoning_tokens") or raw.get("reasoningTokens")
        if reasoning is not None:
            usage["reasoningTokens"] = reasoning
        inp = usage.get("inputTokens") or 0
        outp = usage.get("outputTokens") or 0
        usage["totalTokens"] = inp + outp
    usage["scope"] = "event"
    usage["source"] = "agent_log"
    usage["raw"] = raw if raw else None
    return usage


def _normalize_event(entry: dict, session_id: str) -> dict[str, Any]:
    kind = _event_kind(entry)
    role: str | None = None
    content: Any = None
    summary: str | None = None
    tool_name: str | None = None
    tool_call_id: str | None = None
    parent_id: str | None = None
    msg = entry.get("message", {})

    if kind == "user":
        role = "user"
        content = entry.get("content") or entry.get("text", "")
        summary = _truncate(content)
    elif kind == "assistant":
        role = "assistant"
        content_block = msg
        parts = []
        if isinstance(content_block.get("content"), list):
            for block in content_block["content"]:
                if isinstance(block, dict):
                    text = block.get("text") or block.get("input", "")
                    parts.append(text)
        content = "\n".join(parts) if parts else content_block.get("content", "")
        summary = _truncate(content)
    elif kind == "tool_call":
        role = "assistant"
        tool_name = entry.get("tool_name", "")
        parts = entry.get("parts", [])
        content = parts
        summary = f"Tool: {tool_name}"
    elif kind == "tool_result":
        role = "tool"
        tool_name = entry.get("tool_name", "")
        content = entry.get("content", entry.get("result", ""))
        summary = f"Result: {_truncate(content)}"
    elif kind == "reasoning":
        role = "assistant"
        content = entry.get("content", "")
        summary = _truncate(content)

    event: dict[str, Any] = {
        "agent": "claude",
        "sessionId": session_id,
        "timestamp": entry.get("timestamp"),
        "role": role,
        "kind": kind,
        "content": content,
        "summary": summary,
        "toolName": tool_name,
        "toolCallId": tool_call_id,
        "parentId": parent_id,
        "usage": _normalize_usage(entry),
        "raw": entry,
    }
    return event


def _event_kind(entry: dict) -> str:
    typ = entry.get("type", "")
    if typ == "user":
        return "user"
    if typ == "assistant":
        return "assistant"
    if typ == "tool_call":
        return "tool_call"
    if typ == "tool_result":
        return "tool_result"
    if typ in ("reasoning", "thinking"):
        return "reasoning"
    if typ == "error":
        return "error"
    return "unknown"


def _truncate(text: Any, max_len: int = 120) -> str:
    s = str(text) if text is not None else ""
    return s[:max_len] + ("..." if len(s) > max_len else "")


class ClaudeAdapter(AgentAdapter):
    def __init__(self, projects_dir: Path | None = None) -> None:
        self._projects_dir = projects_dir

    @property
    def name(self) -> str:
        return "claude"

    def default_projects_dir(self) -> Path:
        return Path.home() / ".claude" / "projects"

    @property
    def projects_dir(self) -> Path:
        if self._projects_dir is not None:
            return self._projects_dir
        return self.default_projects_dir()

    @projects_dir.setter
    def projects_dir(self, value: Path) -> None:
        self._projects_dir = value

    def list_projects(self) -> list[dict[str, Any]]:
        result = []
        pd = self.projects_dir
        if not pd.is_dir():
            return result
        for project_path in sorted(pd.iterdir()):
            if not project_path.is_dir():
                continue
            session_infos = []
            for p in project_path.glob("*.jsonl"):
                if not re.fullmatch(r"[0-9a-f-]{36}", p.stem):
                    continue
                first_ts, last_ts = _session_timestamps(p)
                session_infos.append({
                    "id": p.stem,
                    "firstTimestamp": first_ts,
                    "lastTimestamp": last_ts,
                })
            session_infos.sort(key=lambda s: s["lastTimestamp"] or "", reverse=True)
            if session_infos:
                result.append({
                    "projectDir": project_path.name,
                    "sessions": session_infos,
                })
        return result

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for proj in self.list_projects():
            for s in proj.get("sessions", []):
                sessions.append({
                    **s,
                    "projectDir": proj["projectDir"],
                })
        return sessions

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        pd = self.projects_dir
        if not pd.is_dir():
            return None
        for project_path in pd.iterdir():
            if not project_path.is_dir():
                continue
            jsonl_path = project_path / f"{session_id}.jsonl"
            if jsonl_path.exists():
                main_entries = _read_jsonl(jsonl_path)
                session_dir = project_path / session_id
                subagents = _load_subagents(session_dir)
                events = [_normalize_event(e, session_id) for e in main_entries]
                return {
                    "sessionId": session_id,
                    "projectDir": project_path.name,
                    "main": main_entries,
                    "subagents": subagents,
                    "agent": "claude",
                    "events": events,
                }
        return None
