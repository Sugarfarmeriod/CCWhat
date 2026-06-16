from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ccwhat.adapters.base import AgentAdapter, SessionRenameError


_OPCODE_DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
_OPENCODE_DB_PATH = Path.home() / ".local" / "share" / "opencode" / "opencode.db"


def _stable_component(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return "" if value is None else str(value)


def _make_event_id(*parts: Any) -> str:
    key = "ccwhat:opencode:" + "|".join(_stable_component(part) for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _part_event_id(
    session_id: str,
    raw_entry: dict[str, Any],
    part: dict[str, Any],
    part_idx: int,
    suffix: str,
) -> str:
    msg_data = raw_entry.get("message_data", {})
    pdata = part.get("data", {}) if isinstance(part.get("data"), dict) else {}
    message_id = (
        raw_entry.get("message_id")
        or msg_data.get("id")
        or msg_data.get("messageID")
        or raw_entry.get("id")
        or raw_entry.get("time_created")
    )
    part_id = part.get("id") or pdata.get("id") or f"part:{part_idx}"
    return _make_event_id(
        "event",
        session_id,
        message_id,
        part_id,
        pdata.get("type"),
        pdata.get("callID"),
        suffix,
    )


def _truncate(text: Any, max_len: int = 120) -> str:
    s = str(text) if text is not None else ""
    return s[:max_len] + ("..." if len(s) > max_len else "")


def _to_iso_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            number = float(stripped)
        except ValueError:
            return stripped
    else:
        return None

    if number > 10_000_000_000:
        number = number / 1000
    try:
        return datetime.fromtimestamp(number, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (OSError, OverflowError, ValueError):
        return None


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
            if "cacheReadTokens" not in usage:
                cr = cache_raw.get("read") or cache_raw.get("cache_read") or cache_raw.get("read_tokens")
                if cr is not None:
                    usage["cacheReadTokens"] = cr
            if "cacheWriteTokens" not in usage:
                cw = cache_raw.get("write") or cache_raw.get("cache_write") or cache_raw.get("write_tokens")
                if cw is not None:
                    usage["cacheWriteTokens"] = cw
        if "totalTokens" not in usage:
            inp = usage.get("inputTokens")
            outp = usage.get("outputTokens")
            if inp is not None and outp is not None:
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
        self._conn_lock = threading.RLock()

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
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
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
            with self._conn_lock:
                cur = conn.execute(sql, params)
                rows = cur.fetchall()
            return [dict(row) for row in rows]
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return []

    def _query_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        rows = self._query_dicts(sql, params)
        return rows[0] if rows else None

    def list_projects(self) -> list[dict[str, Any]]:
        session_rows = self._query_dicts(
            "SELECT s.id, s.directory AS project_dir, p.name, p.worktree, "
            "s.title, s.agent, s.model, "
            "s.time_created, s.time_updated, s.tokens_input, s.tokens_output "
            "FROM session s "
            "LEFT JOIN project p ON s.project_id = p.id "
            "ORDER BY s.directory, s.time_created DESC"
        )
        seen: dict[str, dict[str, Any]] = {}
        for row in session_rows:
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
            ti = row.get("tokens_input")
            to = row.get("tokens_output")
            raw_agent = row.get("agent") or "opencode"
            sess_data: dict[str, Any] = {
                "id": row["id"],
                "title": row.get("title") or "",
                "displayName": (row.get("title") or "") if row.get("title") else row["id"][:8],
                "canRenameSession": True,
                "agent": "opencode",
                "opencodeAgent": raw_agent,
                "model": row.get("model"),
                "firstTimestamp": _to_iso_timestamp(row.get("time_created")),
                "lastTimestamp": _to_iso_timestamp(row.get("time_updated")),
            }
            if ti is not None:
                sess_data["tokensInput"] = ti
            if to is not None:
                sess_data["tokensOutput"] = to
            seen[d]["sessions"].append(sess_data)
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
            ti = row.get("tokens_input")
            to = row.get("tokens_output")
            raw_agent = row.get("agent") or "opencode"
            sess: dict[str, Any] = {
                "id": row["id"],
                "projectDir": row.get("project_dir") or "",
                "title": row.get("title") or "",
                "displayName": (row.get("title") or "") if row.get("title") else row["id"][:8],
                "canRenameSession": True,
                "agent": "opencode",
                "opencodeAgent": raw_agent,
                "model": row.get("model"),
                "firstTimestamp": _to_iso_timestamp(row.get("time_created")),
                "lastTimestamp": _to_iso_timestamp(row.get("time_updated")),
            }
            if ti is not None:
                sess["tokensInput"] = ti
            if to is not None:
                sess["tokensOutput"] = to
            sessions.append(sess)
        return sessions

    @property
    def can_rename_session(self) -> bool:
        return True

    def rename_session(self, session_id: str, title: str) -> dict[str, Any]:
        """Write title to OpenCode opencode.db session.title."""
        title = title.strip()
        if not title:
            raise SessionRenameError("invalid_title", "Title must not be empty after trimming.")

        db_path = self._get_db_path()
        if db_path is None or not db_path.exists():
            raise SessionRenameError(
                "native_title_unavailable",
                "OpenCode database not found.",
            )

        try:
            conn = sqlite3.connect(str(db_path), timeout=5)
            cur = conn.cursor()
            # Verify schema
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session'")
            if cur.fetchone() is None:
                conn.close()
                raise SessionRenameError(
                    "native_title_unavailable",
                    "OpenCode database missing 'session' table.",
                )
            # Check columns
            cur.execute("PRAGMA table_info(session)")
            columns = {row[1] for row in cur.fetchall()}
            if "id" not in columns or "title" not in columns:
                conn.close()
                raise SessionRenameError(
                    "native_title_unavailable",
                    "OpenCode session table missing 'id' or 'title' column.",
                )
            # Perform update under lock
            with self._conn_lock:
                cur.execute("UPDATE session SET title = ? WHERE id = ?", (title, session_id))
                if cur.rowcount == 0:
                    conn.rollback()
                    conn.close()
                    raise SessionRenameError(
                        "session_not_found",
                        f"No session with id '{session_id}' found in OpenCode DB.",
                    )
                conn.commit()
            conn.close()
        except sqlite3.OperationalError as exc:
            raise SessionRenameError(
                "native_title_write_failed",
                f"OpenCode SQLite write failed: {exc}",
            ) from exc
        except sqlite3.DatabaseError as exc:
            raise SessionRenameError(
                "native_title_write_failed",
                f"OpenCode SQLite error: {exc}",
            ) from exc

        # Reset cached connection so subsequent reads reflect new title
        with self._conn_lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

        return {
            "title": title,
            "displayName": title,
            "canRenameSession": True,
        }

    def raw_to_normalized_events(
        self, raw_entry: dict[str, Any], session_id: str
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        msg_data = raw_entry.get("message_data", {})
        parts = raw_entry.get("parts", [])
        role = msg_data.get("role", "unknown")
        ts = _to_iso_timestamp(raw_entry.get("time_created") or msg_data.get("time", {}).get("created"))

        tokens_raw = msg_data.get("tokens")
        usage = _normalize_usage(tokens_raw)

        if role == "user":
            for part_idx, part in enumerate(parts):
                pdata = part.get("data", {})
                ptype = pdata.get("type", "")
                part_ts = _to_iso_timestamp(part.get("time_created")) or ts
                if ptype == "text":
                    text = pdata.get("text", "")
                    if text:
                        events.append({
                            "id": _part_event_id(session_id, raw_entry, part, part_idx, "text"),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": part_ts,
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
            for part_idx, part in enumerate(parts):
                pdata = part.get("data", {})
                ptype = pdata.get("type", "")
                part_ts = _to_iso_timestamp(part.get("time_created")) or ts
                part_end_ts = _to_iso_timestamp(part.get("time_updated")) or part_ts

                if ptype == "text":
                    text = pdata.get("text", "")
                    if text:
                        events.append({
                            "id": _part_event_id(session_id, raw_entry, part, part_idx, "text"),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": part_ts,
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
                            "id": _part_event_id(session_id, raw_entry, part, part_idx, "reasoning"),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": part_ts,
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
                        raw_state = pdata.get("state")
                        state_time = raw_state.get("time", {}) if isinstance(raw_state, dict) else {}
                        tool_start = _to_iso_timestamp(state_time.get("start")) or part_ts
                        tool_end = _to_iso_timestamp(state_time.get("end")) or part_end_ts
                        events.append({
                            "id": _part_event_id(session_id, raw_entry, part, part_idx, "tool_call"),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": tool_start,
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
                            "id": _part_event_id(session_id, raw_entry, part, part_idx, "tool_result"),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": tool_end,
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
                        "id": _part_event_id(session_id, raw_entry, part, part_idx, ptype),
                        "agent": "opencode",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": part_ts,
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
                            "id": _part_event_id(session_id, raw_entry, part, part_idx, "input"),
                            "agent": "opencode",
                            "sessionId": session_id,
                            "turnId": None,
                            "timestamp": part_ts,
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
                        "id": _part_event_id(session_id, raw_entry, part, part_idx, ptype or "part"),
                        "agent": "opencode",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": part_ts,
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
            turn_id = _make_event_id(
                "turn",
                current_turn[0].get("sessionId"),
                [ev.get("id") for ev in current_turn],
            )
            for ev in current_turn:
                ev["turnId"] = turn_id
            user_summary = ""
            assistant_summary = ""
            turn_usage: dict[str, Any] = {
                "scope": "turn", "source": "derived", "raw": None,
            }
            inp_sum: int | None = None
            outp_sum: int | None = None
            for ev in current_turn:
                u = ev.get("usage", {})
                inp = u.get("inputTokens")
                outp = u.get("outputTokens")
                if inp is not None:
                    inp_sum = (inp_sum or 0) + inp
                if outp is not None:
                    outp_sum = (outp_sum or 0) + outp
                if ev["role"] == "user" and ev["kind"] == "message":
                    user_summary = ev.get("summary", "")
                elif ev["role"] == "assistant" and ev["kind"] == "message":
                    assistant_summary = ev.get("summary", "")
            if inp_sum is not None:
                turn_usage["inputTokens"] = inp_sum
            if outp_sum is not None:
                turn_usage["outputTokens"] = outp_sum
            if inp_sum is not None and outp_sum is not None:
                turn_usage["totalTokens"] = inp_sum + outp_sum
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
            "SELECT id, message_id, session_id, time_created, time_updated, data FROM part "
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
                        "time_created": _to_iso_timestamp(sm_data.get("time", {}).get("created")),
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
                        "time_created": _to_iso_timestamp(sm_data.get("time", {}).get("created")),
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
                    "time_created": _to_iso_timestamp(mr["time_created"]),
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
                    "time_created": _to_iso_timestamp(mr["time_created"]),
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
            "tokens_cache_read, tokens_cache_write, cost, time_created, time_updated "
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
            "scope": "session",
            "source": "agent_log",
            "raw": None,
        }
        for key, col in (
            ("inputTokens", "tokens_input"),
            ("outputTokens", "tokens_output"),
            ("reasoningTokens", "tokens_reasoning"),
            ("cacheReadTokens", "tokens_cache_read"),
            ("cacheWriteTokens", "tokens_cache_write"),
        ):
            val = session_row.get(col)
            if val is not None:
                usage[key] = val
        inp = usage.get("inputTokens")
        outp = usage.get("outputTokens")
        if inp is not None and outp is not None:
            usage["totalTokens"] = inp + outp

        native_title = session_row.get("title") or ""
        display = native_title if native_title else session_id[:8]
        result: dict[str, Any] = {
            "sessionId": session_id,
            "projectDir": project_dir,
            "main": [],
            "subagents": [],
            "agent": "opencode",
            "events": events,
            "turns": turns,
            "usage": usage,
            "title": native_title,
            "displayName": display,
            "canRenameSession": True,
            "firstTimestamp": _to_iso_timestamp(session_row.get("time_created")),
            "lastTimestamp": _to_iso_timestamp(session_row.get("time_updated")),
            "_metadata": {
                "title": native_title,
                "model": model_info,
                "cost": session_row.get("cost") or 0,
                "opencodeAgent": agent_name,
            },
        }
        return result
