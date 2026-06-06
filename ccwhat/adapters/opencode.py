from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from ccwhat.adapters.base import AgentAdapter


_OPCODE_DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
_OPENCODE_DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def _make_event_id() -> str:
    return str(uuid.uuid4())


def _truncate(text: Any, max_len: int = 120) -> str:
    s = str(text) if text is not None else ""
    return s[:max_len] + ("..." if len(s) > max_len else "")


def _normalize_usage(
    raw: dict[str, Any] | None,
    scope: str = "event",
    source: str = "agent_log",
) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    if raw:
        mappings = {
            "inputTokens": ["input", "input_tokens", "inputTokens"],
            "outputTokens": ["output", "output_tokens", "outputTokens"],
            "reasoningTokens": ["reasoning", "reasoning_tokens", "reasoningTokens"],
            "cacheReadTokens": ["cacheReadTokens", "cache_read", "cache_read_tokens"],
            "cacheWriteTokens": ["cacheWriteTokens", "cache_write", "cache_write_tokens"],
            "totalTokens": ["total", "total_tokens", "totalTokens"],
        }
        for key, candidates in mappings.items():
            for c in candidates:
                val = raw.get(c)
                if val is not None:
                    usage[key] = val
                    break
        cache_raw = raw.get("cache")
        if cache_raw and isinstance(cache_raw, dict):
            if "inputTokens" not in usage:
                cr = cache_raw.get("read") or cache_raw.get("cache_read") or cache_raw.get("read_tokens")
                if cr is not None:
                    usage["cacheReadTokens"] = cr
            if "outputTokens" not in usage:
                cw = cache_raw.get("write") or cache_raw.get("cache_write") or cache_raw.get("write_tokens")
                if cw is not None:
                    usage["cacheWriteTokens"] = cw
        if "totalTokens" not in usage:
            inp = usage.get("inputTokens") or 0
            outp = usage.get("outputTokens") or 0
            if inp or outp:
                usage["totalTokens"] = inp + outp
    usage["scope"] = scope
    usage["source"] = source
    usage["raw"] = raw
    return usage


def _find_tool_state(part_data: dict[str, Any]) -> dict[str, Any] | None:
    state = part_data.get("state") or part_data.get("result") or {}
    if not isinstance(state, dict):
        return None
    content_input = state.get("input") or {}
    content_output = state.get("output") or ""
    content_error = state.get("error") or ""
    status = state.get("status", "unknown")
    tool_server = state.get("tool_server") or state.get("server")
    return {
        "status": status,
        "input": content_input,
        "output": content_output,
        "error": content_error,
        "toolServer": tool_server,
    }


class OpenCodeAdapter(AgentAdapter):
    def __init__(self, projects_dir: Path | None = None) -> None:
        self._projects_dir = projects_dir
        self._conn: sqlite3.Connection | None = None

    @property
    def name(self) -> str:
        return "opencode"

    def default_projects_dir(self) -> Path:
        return _OPENCODE_DB_PATH

    @property
    def projects_dir(self) -> Path:
        if self._projects_dir is not None:
            return self._projects_dir
        return self.default_projects_dir()

    @projects_dir.setter
    def projects_dir(self, value: Path) -> None:
        self._projects_dir = value

    def _get_db_path(self) -> Path | None:
        pd = self.projects_dir
        if pd.is_file() and pd.suffix in (".db", ".sqlite", ".sqlite3"):
            return pd
        maybe = pd / "opencode.db"
        if maybe.is_file():
            return maybe
        alt = pd / "opencode.sqlite"
        if alt.is_file():
            return alt
        return None

    def _connect(self) -> sqlite3.Connection | None:
        if self._conn is not None:
            return self._conn
        db_path = self._get_db_path()
        if db_path is None:
            return None
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            self._conn = conn
            return conn
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return None

    def _query_dicts(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        conn = self._connect()
        if conn is None:
            return []
        try:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return []

    def _query_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        rows = self._query_dicts(sql, params)
        return rows[0] if rows else None

    def list_projects(self) -> list[dict[str, Any]]:
        rows = self._query_dicts(
            "SELECT DISTINCT s.directory AS project_dir, p.name, p.worktree "
            "FROM session s "
            "LEFT JOIN project p ON s.project_id = p.id "
            "ORDER BY s.directory"
        )
        seen: dict[str, dict[str, Any]] = {}
        for row in rows:
            d = row.get("project_dir") or row.get("worktree") or ""
            if not d:
                continue
            if d not in seen:
                seen[d] = {
                    "projectDir": d,
                    "projectName": row.get("name") or Path(d).name,
                    "worktree": row.get("worktree") or d,
                    "sessions": [],
                }
        return list(seen.values())

    def list_sessions(self) -> list[dict[str, Any]]:
        rows = self._query_dicts(
            "SELECT s.id, s.directory AS project_dir, s.title, s.agent, s.model, "
            "s.time_created, s.time_updated, s.tokens_input, s.tokens_output, "
            "s.tokens_reasoning, s.tokens_cache_read, s.tokens_cache_write "
            "FROM session s ORDER BY s.time_created DESC LIMIT 500"
        )
        sessions: list[dict[str, Any]] = []
        for row in rows:
            sessions.append({
                "id": row["id"],
                "projectDir": row.get("project_dir") or "",
                "title": row.get("title") or "",
                "agent": row.get("agent") or "opencode",
                "model": row.get("model"),
                "firstTimestamp": str(row.get("time_created") or ""),
                "lastTimestamp": str(row.get("time_updated") or ""),
                "tokensInput": row.get("tokens_input") or 0,
                "tokensOutput": row.get("tokens_output") or 0,
            })
        return sessions

    def raw_to_normalized_events(
        self, raw_entry: dict[str, Any], session_id: str
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        msg_data = raw_entry.get("message_data", {})
        parts = raw_entry.get("parts", [])
        role = msg_data.get("role", "unknown")
        ts = raw_entry.get("time_created") or msg_data.get("time", {}).get("created")

        tokens_raw = msg_data.get("tokens")
        usage = _normalize_usage(tokens_raw)

        if role == "user":
            for part in parts:
                pdata = part.get("data", {})
                ptype = pdata.get("type", "")
                if ptype == "text":
                    text = pdata.get("text", "")
                    if text:
                        events.append({
                            "id": _make_event_id(),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "user",
                            "kind": "message",
                            "content": text,
                            "summary": _truncate(text),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": msg_data.get("parentID"),
                            "usage": _normalize_usage(None),
                            "raw": raw_entry,
                        })

        elif role == "assistant":
            for part in parts:
                pdata = part.get("data", {})
                ptype = pdata.get("type", "")

                if ptype == "text":
                    text = pdata.get("text", "")
                    if text:
                        events.append({
                            "id": _make_event_id(),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "message",
                            "content": text,
                            "summary": _truncate(text),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": msg_data.get("parentID"),
                            "usage": _normalize_usage(None),
                            "raw": raw_entry,
                        })

                elif ptype == "reasoning":
                    text = pdata.get("text", "")
                    if text:
                        events.append({
                            "id": _make_event_id(),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "reasoning",
                            "content": text,
                            "summary": _truncate(text),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": msg_data.get("parentID"),
                            "usage": _normalize_usage(None),
                            "raw": raw_entry,
                        })

                elif ptype == "tool":
                    tool_name = pdata.get("tool", "")
                    call_id = pdata.get("callID", "")
                    tool_state = _find_tool_state(pdata)
                    if tool_state and tool_state["status"] == "completed":
                        events.append({
                            "id": _make_event_id(),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "assistant",
                            "kind": "tool_call",
                            "content": tool_state.get("input", {}),
                            "summary": f"Tool: {tool_name}",
                            "toolName": tool_name,
                            "toolCallId": call_id,
                            "parentId": msg_data.get("parentID"),
                            "usage": _normalize_usage(None),
                            "raw": raw_entry,
                        })
                        events.append({
                            "id": _make_event_id(),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "tool",
                            "kind": "tool_result",
                            "content": tool_state.get("output", ""),
                            "summary": _truncate(tool_state.get("output", "")),
                            "toolName": tool_name,
                            "toolCallId": call_id,
                            "parentId": msg_data.get("parentID"),
                            "usage": _normalize_usage(None),
                            "raw": raw_entry,
                        })

                elif ptype in ("step-start", "step-finish"):
                    sub_kind = pdata.get("type", "")
                    reason = pdata.get("reason", "")
                    step_tokens = pdata.get("tokens")
                    sub_usage = _normalize_usage(step_tokens) if step_tokens else None
                    events.append({
                        "id": _make_event_id(),
                        "agent": "opencode",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": ts,
                        "role": None,
                        "kind": "step",
                        "content": {"reason": reason} if reason else None,
                        "summary": sub_kind,
                        "toolName": None,
                        "toolCallId": None,
                        "parentId": msg_data.get("parentID"),
                        "usage": sub_usage or _normalize_usage(None),
                        "raw": raw_entry,
                    })

                elif ptype == "input":
                    text = pdata.get("text", "")
                    if text:
                        events.append({
                            "id": _make_event_id(),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": ts,
                            "role": "user",
                            "kind": "message",
                            "content": text,
                            "summary": _truncate(text),
                            "toolName": None,
                            "toolCallId": None,
                            "parentId": msg_data.get("parentID"),
                            "usage": _normalize_usage(None),
                            "raw": raw_entry,
                        })

                else:
                    events.append({
                        "id": _make_event_id(),
                        "agent": "opencode",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": ts,
                        "role": role,
                        "kind": ptype,
                        "content": pdata,
                        "summary": f"part: {ptype}",
                        "toolName": None,
                        "toolCallId": None,
                        "parentId": msg_data.get("parentID"),
                        "usage": _normalize_usage(None),
                        "raw": raw_entry,
                    })

        if events and usage.get("totalTokens"):
            for ev in events:
                if ev["role"] == "assistant":
                    ev["usage"] = usage
                    break

        return events

    def _build_turns(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        turns: list[dict[str, Any]] = []
        current_turn: list[dict[str, Any]] = []
        turn_start_ts: str | None = None

        def flush_turn() -> None:
            nonlocal current_turn, turn_start_ts
            if not current_turn:
                return
            turn_id = _make_event_id()
            for ev in current_turn:
                ev["turnId"] = turn_id
            user_summary = ""
            assistant_summary = ""
            turn_usage: dict[str, Any] = {
                "inputTokens": 0, "outputTokens": 0, "totalTokens": 0,
                "scope": "turn", "source": "derived", "raw": None,
            }
            for ev in current_turn:
                u = ev.get("usage", {})
                inp = u.get("inputTokens") or 0
                outp = u.get("outputTokens") or 0
                turn_usage["inputTokens"] += inp
                turn_usage["outputTokens"] += outp
                if ev["role"] == "user" and ev["kind"] == "message":
                    user_summary = ev.get("summary", "")
                elif ev["role"] == "assistant" and ev["kind"] == "message":
                    assistant_summary = ev.get("summary", "")
            turn_usage["totalTokens"] = turn_usage["inputTokens"] + turn_usage["outputTokens"]
            ended_at = current_turn[-1].get("timestamp") if current_turn else None
            turns.append({
                "id": turn_id,
                "sessionId": current_turn[0].get("sessionId") if current_turn else None,
                "agent": "opencode",
                "startedAt": turn_start_ts,
                "endedAt": ended_at,
                "userSummary": user_summary or "",
                "assistantSummary": assistant_summary or "",
                "events": list(current_turn),
                "usage": turn_usage,
            })
            current_turn = []
            turn_start_ts = None

        for ev in events:
            if ev["role"] == "user" and ev["kind"] == "message":
                flush_turn()
                turn_start_ts = ev.get("timestamp")
                current_turn.append(ev)
            else:
                if not current_turn:
                    turn_start_ts = ev.get("timestamp")
                current_turn.append(ev)

        flush_turn()
        return turns

    def _load_messages_and_parts(
        self, session_id: str
    ) -> list[dict[str, Any]]:
        msg_rows = self._query_dicts(
            "SELECT id, session_id, time_created, data FROM message "
            "WHERE session_id = ? ORDER BY time_created ASC",
            (session_id,),
        )
        session_msg_rows = self._query_dicts(
            "SELECT id, session_id, type, seq, data FROM session_message "
            "WHERE session_id = ? ORDER BY seq ASC",
            (session_id,),
        )
        part_rows = self._query_dicts(
            "SELECT id, message_id, session_id, time_created, data FROM part "
            "WHERE session_id = ? ORDER BY time_created ASC",
            (session_id,),
        )
        parts_by_msg: dict[str, list[dict[str, Any]]] = {}
        for p in part_rows:
            raw_data = p.get("data", "{}")
            parsed_data = raw_data
            if isinstance(raw_data, str):
                try:
                    parsed_data = json.loads(raw_data)
                except (json.JSONDecodeError, TypeError):
                    parsed_data = {}
            p_copy = dict(p)
            p_copy["data"] = parsed_data
            mid = p.get("message_id", "")
            if mid not in parts_by_msg:
                parts_by_msg[mid] = []
            parts_by_msg[mid].append(p_copy)

        ordered: list[dict[str, Any]] = []
        has_session_msg = bool(session_msg_rows)

        if has_session_msg:
            used_msg_ids: set[str] = set()
            for sm in session_msg_rows:
                sm_type = sm.get("type", "")
                sm_data_s = sm.get("data", "{}")
                try:
                    sm_data = json.loads(sm_data_s) if isinstance(sm_data_s, str) else sm_data_s
                except (json.JSONDecodeError, TypeError):
                    sm_data = {}
                if sm_type in ("agent-switched", "model-switched"):
                    model_info = sm_data.get("model")
                    agent_info = sm_data.get("agent")
                    ordered.append({
                        "time_created": sm_data.get("time", {}).get("created"),
                        "message_id": sm["id"],
                        "message_data": {
                            "role": None,
                            "type": sm_type,
                            "agent": agent_info,
                            "model": model_info,
                        },
                        "parts": [],
                    })
                    used_msg_ids.add(sm["id"])
                elif sm_type in ("chat", "input", "response"):
                    msg_id = sm["id"]
                    msg_data = {}
                    try:
                        msg_data = json.loads(sm_data_s) if isinstance(sm_data_s, str) else sm_data_s
                    except (json.JSONDecodeError, TypeError):
                        msg_data = {}
                    msg_data.setdefault("role", "user" if sm_type == "input" else "assistant")
                    ordered.append({
                        "time_created": sm_data.get("time", {}).get("created"),
                        "message_id": msg_id,
                        "message_data": msg_data,
                        "parts": parts_by_msg.get(msg_id, []),
                    })
                    used_msg_ids.add(msg_id)

            for mr in msg_rows:
                mid = mr["id"]
                if mid in used_msg_ids:
                    continue
                try:
                    md = json.loads(mr["data"]) if isinstance(mr["data"], str) else mr["data"]
                except (json.JSONDecodeError, TypeError):
                    md = {}
                ordered.append({
                    "time_created": mr["time_created"],
                    "message_id": mid,
                    "message_data": md,
                    "parts": parts_by_msg.get(mid, []),
                })
        else:
            for mr in msg_rows:
                try:
                    md = json.loads(mr["data"]) if isinstance(mr["data"], str) else mr["data"]
                except (json.JSONDecodeError, TypeError):
                    md = {}
                ordered.append({
                    "time_created": mr["time_created"],
                    "message_id": mr["id"],
                    "message_data": md,
                    "parts": parts_by_msg.get(mr["id"], []),
                })

        ordered.sort(key=lambda x: x["time_created"] or 0)
        return ordered

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        session_row = self._query_one(
            "SELECT id, project_id, directory, title, agent, model, "
            "tokens_input, tokens_output, tokens_reasoning, "
            "tokens_cache_read, tokens_cache_write, cost, time_created "
            "FROM session WHERE id = ?",
            (session_id,),
        )
        if session_row is None:
            return None

        project_dir = session_row.get("directory") or session_row.get("path") or ""

        model_str = session_row.get("model") or "{}"
        if isinstance(model_str, str):
            try:
                model_info = json.loads(model_str)
            except (json.JSONDecodeError, TypeError):
                model_info = {}
        else:
            model_info = model_str

        agent_name = session_row.get("agent") or "opencode"

        raw_entries = self._load_messages_and_parts(session_id)

        events: list[dict[str, Any]] = []
        for entry in raw_entries:
            events.extend(self.raw_to_normalized_events(entry, session_id))

        turns = self._build_turns(events)

        usage: dict[str, Any] = {
            "inputTokens": session_row.get("tokens_input") or 0,
            "outputTokens": session_row.get("tokens_output") or 0,
            "reasoningTokens": session_row.get("tokens_reasoning") or 0,
            "cacheReadTokens": session_row.get("tokens_cache_read") or 0,
            "cacheWriteTokens": session_row.get("tokens_cache_write") or 0,
            "scope": "session",
            "source": "agent_log",
            "raw": None,
        }
        total = (
            usage["inputTokens"]
            + usage["outputTokens"]
            + usage["reasoningTokens"]
        )
        usage["totalTokens"] = total or (
            usage["inputTokens"] + usage["outputTokens"]
        )

        result: dict[str, Any] = {
            "sessionId": session_id,
            "projectDir": project_dir,
            "main": [],
            "subagents": [],
            "agent": agent_name,
            "events": events,
            "turns": turns,
            "usage": usage,
            "_metadata": {
                "title": session_row.get("title") or "",
                "model": model_info,
                "cost": session_row.get("cost") or 0,
            },
        }
        return result
