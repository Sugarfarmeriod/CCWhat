from __future__ import annotations

import json
import re
import uuid
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


def _normalize_usage_helper(raw_usage: dict[str, Any] | None, scope: str = "event", source: str = "agent_log") -> dict[str, Any]:
    usage: dict[str, Any] = {}
    if raw_usage:
        fields = {
            "inputTokens": ("input_tokens", "inputTokens"),
            "outputTokens": ("output_tokens", "outputTokens"),
            "reasoningTokens": ("reasoning_tokens", "reasoning_output_tokens", "reasoningTokens"),
            "cacheReadTokens": ("cache_read_input_tokens", "cacheReadInputTokens"),
            "cacheWriteTokens": ("cache_write_input_tokens", "cacheWriteInputTokens"),
            "cacheCreationTokens": ("cache_creation_input_tokens", "cacheCreationTokens"),
            "cachedInputTokens": ("cached_input_tokens", "cachedInputTokens"),
        }
        for key, candidates in fields.items():
            for c in candidates:
                val = raw_usage.get(c)
                if val is not None:
                    usage[key] = val
                    break

        total = raw_usage.get("total_tokens") or raw_usage.get("totalTokens")
        if total is not None:
            usage["totalTokens"] = total
        elif "inputTokens" in usage and "outputTokens" in usage:
            inp = usage.get("inputTokens")
            outp = usage.get("outputTokens")
            if inp is not None and outp is not None:
                usage["totalTokens"] = inp + outp

    usage["scope"] = scope
    usage["source"] = source
    usage["raw"] = raw_usage if raw_usage else None
    return usage


def _make_event_id() -> str:
    return str(uuid.uuid4())


def _truncate(text: Any, max_len: int = 120) -> str:
    s = str(text) if text is not None else ""
    s_str = str(s)
    return s_str[:max_len] + ("..." if len(s_str) > max_len else "")


def _block_text(block: dict[str, Any]) -> str:
    content = block.get("text") or block.get("input", "")
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    return str(content)


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

    def raw_to_normalized_events(self, raw_entry: dict[str, Any], session_id: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        typ = raw_entry.get("type", "")
        ts = raw_entry.get("timestamp")
        msg = raw_entry.get("message", {})
        content_list = msg.get("content") if isinstance(msg.get("content"), list) else None
        raw_usage = msg.get("usage") or raw_entry.get("usage")

        if typ == "user":
            if content_list and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content_list):
                for block in content_list:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_result":
                        tool_use_id = block.get("tool_use_id", "")
                        tool_name = block.get("name") or ""
                        content = block.get("content") or block.get("input", "")
                        events.append({
                            "id": _make_event_id(),
                            "agent": "claude",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "tool",
                            "kind": "tool_result",
                            "content": content,
                            "summary": _truncate(content),
                            "toolName": tool_name,
                            "toolCallId": tool_use_id,
                            "parentId": None,
                            "usage": _normalize_usage_helper(None),
                            "raw": raw_entry,
                        })
                    else:
                        events.append({
                            "id": _make_event_id(),
                            "agent": "claude",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "user",
                            "kind": "message",
                            "content": _block_text(block),
                            "summary": _truncate(block.get("text", "")),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": None,
                            "usage": _normalize_usage_helper(None),
                            "raw": raw_entry,
                        })
            else:
                raw_text = raw_entry.get("content") or raw_entry.get("text", "")
                if isinstance(raw_text, list):
                    raw_text = " ".join(str(x) for x in raw_text)
                events.append({
                    "id": _make_event_id(),
                    "agent": "claude",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "user",
                    "kind": "message",
                    "content": str(raw_text),
                    "summary": _truncate(raw_text),
                    "toolName": None,
                    "toolCallId": None,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })

        elif typ == "assistant":
            if content_list:
                for block in content_list:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        text = block.get("text", "")
                        events.append({
                            "id": _make_event_id(),
                            "agent": "claude",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "message",
                            "content": text,
                            "summary": _truncate(text),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": None,
                            "usage": _normalize_usage_helper(raw_usage),
                            "raw": raw_entry,
                        })
                    elif btype == "tool_use":
                        tool_name = block.get("name", "")
                        tool_call_id = block.get("id", "")
                        inp = block.get("input", {})
                        events.append({
                            "id": _make_event_id(),
                            "agent": "claude",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "tool_call",
                            "content": inp,
                            "summary": f"Tool: {tool_name}",
                            "toolName": tool_name,
                            "toolCallId": tool_call_id,
                            "parentId": None,
                            "usage": _normalize_usage_helper(None),
                            "raw": raw_entry,
                        })
                    elif btype in ("thinking", "reasoning"):
                        r_content = block.get("thinking", "") or block.get("text", "") or block.get("content", "")
                        events.append({
                            "id": _make_event_id(),
                            "agent": "claude",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "reasoning",
                            "content": r_content,
                            "summary": _truncate(r_content),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": None,
                            "usage": _normalize_usage_helper(None),
                            "raw": raw_entry,
                        })
                    else:
                        events.append({
                            "id": _make_event_id(),
                            "agent": "claude",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "unknown",
                            "content": block,
                            "summary": f"block: {btype}",
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": None,
                            "usage": _normalize_usage_helper(None),
                            "raw": raw_entry,
                        })
            else:
                text = msg.get("content") or raw_entry.get("content", "")
                if isinstance(text, list):
                    text = " ".join(str(x) for x in text)
                events.append({
                    "id": _make_event_id(),
                    "agent": "claude",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "assistant",
                    "kind": "message",
                    "content": str(text),
                    "summary": _truncate(text),
                    "toolName": None,
                    "toolCallId": None,
                    "parentId": None,
                    "usage": _normalize_usage_helper(raw_usage),
                    "raw": raw_entry,
                })

        elif typ == "tool_result":
            events.append({
                "id": _make_event_id(),
                "agent": "claude",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": "tool",
                "kind": "tool_result",
                "content": raw_entry.get("content", raw_entry.get("result", "")),
                "summary": _truncate(raw_entry.get("content", "")),
                "toolName": raw_entry.get("tool_name", ""),
                "toolCallId": raw_entry.get("tool_call_id", ""),
                "parentId": None,
                "usage": _normalize_usage_helper(None),
                "raw": raw_entry,
            })

        elif typ in ("reasoning", "thinking"):
            r_content = raw_entry.get("content", "")
            events.append({
                "id": _make_event_id(),
                "agent": "claude",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": "assistant",
                "kind": "reasoning",
                "content": r_content,
                "summary": _truncate(r_content),
                "toolName": None,
                "toolCallId": None,
                "parentId": None,
                "usage": _normalize_usage_helper(None),
                "raw": raw_entry,
            })

        elif typ == "error":
            events.append({
                "id": _make_event_id(),
                "agent": "claude",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": "system",
                "kind": "error",
                "content": raw_entry.get("content", raw_entry.get("error", "")),
                "summary": _truncate(raw_entry.get("content", "")),
                "toolName": None,
                "toolCallId": None,
                "parentId": None,
                "usage": _normalize_usage_helper(None),
                "raw": raw_entry,
            })

        else:
            events.append({
                "id": _make_event_id(),
                "agent": "claude",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": None,
                "kind": "unknown",
                "content": raw_entry,
                "summary": None,
                "toolName": None,
                "toolCallId": None,
                "parentId": None,
                "usage": _normalize_usage_helper(None),
                "raw": raw_entry,
            })

        return events

    def _build_turns(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        turns: list[dict[str, Any]] = []
        current_turn: list[dict[str, Any]] = []
        turn_start_ts: str | None = None
        turn_user_event: dict[str, Any] | None = None

        def flush_turn() -> None:
            nonlocal current_turn, turn_start_ts, turn_user_event
            if not current_turn:
                return
            turn_id = _make_event_id()
            for ev in current_turn:
                ev["turnId"] = turn_id
            user_msg = turn_user_event
            user_summary = ""
            assistant_summary = ""
            turn_usage: dict[str, Any] = {
                "inputTokens": 0,
                "outputTokens": 0,
                "totalTokens": 0,
                "scope": "turn",
                "source": "derived",
                "raw": None,
            }
            for ev in current_turn:
                u = ev.get("usage", {})
                inp = u.get("inputTokens") or 0
                outp = u.get("outputTokens") or 0
                turn_usage["inputTokens"] += inp
                turn_usage["outputTokens"] += outp
                if ev["kind"] == "message" and ev["role"] == "user":
                    user_summary = ev.get("summary", "") or ""
                elif ev["kind"] == "message" and ev["role"] == "assistant":
                    assistant_summary = ev.get("summary", "") or ""
            turn_usage["totalTokens"] = turn_usage["inputTokens"] + turn_usage["outputTokens"]

            ended_at = current_turn[-1].get("timestamp") if current_turn else None
            turns.append({
                "id": turn_id,
                "sessionId": current_turn[0].get("sessionId") if current_turn else None,
                "agent": "claude",
                "startedAt": turn_start_ts,
                "endedAt": ended_at,
                "userSummary": user_summary,
                "assistantSummary": assistant_summary,
                "events": list(current_turn),
                "usage": turn_usage,
            })
            current_turn = []
            turn_start_ts = None
            turn_user_event = None

        for ev in events:
            if ev["role"] == "user" and ev["kind"] == "message":
                flush_turn()
                turn_start_ts = ev.get("timestamp")
                turn_user_event = ev
                current_turn.append(ev)
            elif ev["role"] == "user" and ev["kind"] == "tool_result":
                if not current_turn and turn_user_event is None:
                    turn_start_ts = ev.get("timestamp")
                current_turn.append(ev)
            else:
                if not current_turn:
                    turn_start_ts = ev.get("timestamp")
                current_turn.append(ev)

        flush_turn()
        return turns

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
                events: list[dict[str, Any]] = []
                for e in main_entries:
                    events.extend(self.raw_to_normalized_events(e, session_id))
                turns = self._build_turns(events)
                return {
                    "sessionId": session_id,
                    "projectDir": project_path.name,
                    "main": main_entries,
                    "subagents": subagents,
                    "agent": "claude",
                    "events": events,
                    "turns": turns,
                }
        return None
