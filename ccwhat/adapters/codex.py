from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from ccwhat.adapters.base import AgentAdapter


_SESSION_ID_RE = re.compile(
    r"rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-"
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
)

_CODEX_SESSIONS_DIR = Path.home() / ".codex" / "sessions"
_CODEX_SQLITE_PATH = Path.home() / ".codex" / "state_5.sqlite"


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


def _stable_component(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return "" if value is None else str(value)


def _make_event_id(*parts: Any) -> str:
    key = "ccwhat:codex:" + "|".join(_stable_component(part) for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _raw_event_anchor(raw_entry: dict[str, Any]) -> str:
    payload = raw_entry.get("payload", {})
    if raw_entry.get("_fileLine") is not None:
        return f"line:{raw_entry.get('_fileLine')}"
    return _stable_component({
        "type": raw_entry.get("type"),
        "timestamp": raw_entry.get("timestamp"),
        "payload_type": payload.get("type") if isinstance(payload, dict) else None,
        "payload_id": payload.get("id") if isinstance(payload, dict) else None,
        "call_id": payload.get("call_id") if isinstance(payload, dict) else None,
        "payload": payload,
    })


def _codex_event_id(raw_entry: dict[str, Any], session_id: str, suffix: str) -> str:
    return _make_event_id("event", session_id, _raw_event_anchor(raw_entry), suffix)


def _truncate(text: Any, max_len: int = 120) -> str:
    s = str(text) if text is not None else ""
    return s[:max_len] + ("..." if len(s) > max_len else "")


_CONTEXT_BLOB_MARKERS = (
    "<environment_context>",
    "<codex_internal_context",
    "<permissions instructions>",
    "<app-context>",
    "<apps_instructions>",
    "<skills_instructions>",
    "<plugins_instructions>",
    "<collaboration_mode>",
)


def _content_blocks_text(content_blocks: Any, text_types: tuple[str, ...]) -> str:
    parts: list[str] = []
    for block in content_blocks if isinstance(content_blocks, list) else [content_blocks]:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") in text_types:
            parts.append(str(block.get("text", "")))
    return "\n".join(part for part in parts if part).strip()


def _is_context_blob(text: str) -> bool:
    stripped = text.lstrip()
    lowered = stripped.lower()
    return any(lowered.startswith(marker.lower()) for marker in _CONTEXT_BLOB_MARKERS)


def _metadata_event(
    raw_entry: dict[str, Any],
    session_id: str,
    summary: str,
    content: Any = None,
) -> dict[str, Any]:
    return {
        "id": _codex_event_id(raw_entry, session_id, summary),
        "agent": "codex",
        "sessionId": session_id,
        "turnId": None,
        "timestamp": raw_entry.get("timestamp"),
        "role": None,
        "kind": "metadata",
        "content": content,
        "summary": summary,
        "toolName": None,
        "toolCallId": None,
        "parentId": None,
        "usage": _normalize_usage_helper(None),
        "raw": raw_entry,
    }


def _normalize_usage_helper(
    raw_usage: dict[str, Any] | None, scope: str = "event", source: str = "agent_log"
) -> dict[str, Any]:
    usage: dict[str, Any] = {}
    if raw_usage:
        fields = {
            "inputTokens": ("input_tokens", "inputTokens"),
            "outputTokens": ("output_tokens", "outputTokens"),
            "reasoningTokens": ("reasoning_output_tokens", "reasoning_tokens", "reasoningTokens"),
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
        total = raw_usage.get("total_tokens") or raw_usage.get("totalTokens") or raw_usage.get("tokens_used")
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


def _extract_session_id(filename: str) -> str | None:
    m = _SESSION_ID_RE.search(filename)
    if m:
        return m.group(1)
    return None


def _safe_parse_json(val: Any) -> Any:
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return val


def _cwd_from_entries(entries: list[dict]) -> str | None:
    for entry in entries:
        if entry.get("type") == "turn_context":
            cwd = entry.get("payload", {}).get("cwd")
            if cwd:
                return cwd
        if entry.get("type") == "response_item":
            payload = entry.get("payload", {})
            if payload.get("role") == "user":
                content = payload.get("content", [])
                for block in content if isinstance(content, list) else [content]:
                    if isinstance(block, dict) and block.get("type") == "input_text":
                        text = block.get("text", "")
                        m = re.search(r"<cwd>([^<]+)</cwd>", text)
                        if m:
                            return m.group(1).strip()
    return None


class CodexAdapter(AgentAdapter):
    def __init__(self, projects_dir: Path | None = None) -> None:
        self._projects_dir = projects_dir
        self._sqlite_path: Path | None = None
        self._sqlite_cache: dict[str, dict[str, Any]] | None = None

    @property
    def name(self) -> str:
        return "codex"

    def default_projects_dir(self) -> Path:
        return _CODEX_SESSIONS_DIR

    @property
    def projects_dir(self) -> Path:
        if self._projects_dir is not None:
            return self._projects_dir
        return self.default_projects_dir()

    @projects_dir.setter
    def projects_dir(self, value: Path) -> None:
        self._projects_dir = value

    def _get_sqlite_path(self) -> Path | None:
        if self._sqlite_path is not None:
            return self._sqlite_path
        sp = _CODEX_SQLITE_PATH
        if sp.exists():
            return sp
        return None

    def _load_sqlite_metadata(self) -> dict[str, dict[str, Any]]:
        if self._sqlite_cache is not None:
            return self._sqlite_cache
        result: dict[str, dict[str, Any]] = {}
        sp = self._get_sqlite_path()
        if sp is None:
            self._sqlite_cache = result
            return result
        try:
            conn = sqlite3.connect(str(sp))
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, cwd, model, model_provider, updated_at, tokens_used, "
                "created_at, rollout_path FROM threads LIMIT 10000"
            )
            for row in cur.fetchall():
                tid = str(row[0]) if row[0] else ""
                meta: dict[str, Any] = {}
                if row[1]:
                    meta["title"] = row[1]
                if row[2]:
                    meta["cwd"] = row[2]
                if row[3]:
                    meta["model"] = row[3]
                if row[4]:
                    meta["provider"] = row[4]
                if row[5]:
                    meta["updated_at"] = row[5]
                if row[6]:
                    meta["tokens_used"] = row[6]
                if len(row) > 7 and row[7]:
                    meta["created_at"] = row[7]
                if len(row) > 8 and row[8]:
                    meta["rollout_path"] = row[8]
                result[tid] = meta
            conn.close()
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            pass
        self._sqlite_cache = result
        return result

    def _cwd_from_file(self, path: Path) -> str | None:
        entries = _read_jsonl(path)
        return _cwd_from_entries(entries)

    def _lookup_sqlite_cwd(self, sid: str) -> str | None:
        meta = self._load_sqlite_metadata().get(sid, {})
        return meta.get("cwd")

    def _session_project_dir(self, path: Path, sid: str) -> str:
        cwd = self._cwd_from_file(path)
        if cwd:
            return cwd
        sqlite_cwd = self._lookup_sqlite_cwd(sid)
        if sqlite_cwd:
            return sqlite_cwd
        pd = self.projects_dir
        if pd.is_dir():
            try:
                rel = path.relative_to(pd)
                return str(rel.parent)
            except ValueError:
                pass
        return str(path.parent)

    def _scan_rollout_files(
        self,
    ) -> list[tuple[Path, str, str]]:
        results: list[tuple[Path, str, str]] = []
        pd = self.projects_dir
        if not pd.is_dir():
            return results
        year_dirs = sorted(pd.iterdir())
        for yd in year_dirs:
            if not yd.is_dir() or not yd.name.isdigit():
                continue
            for md in sorted(yd.iterdir()):
                if not md.is_dir() or not md.name.isdigit():
                    continue
                for dd in sorted(md.iterdir()):
                    if not dd.is_dir() or not dd.name.isdigit():
                        continue
                    for f in sorted(dd.iterdir()):
                        if not f.name.startswith("rollout-") or not f.name.endswith(".jsonl"):
                            continue
                        sid = _extract_session_id(f.name)
                        if sid is None:
                            continue
                        project_dir = self._session_project_dir(f, sid)
                        results.append((f, sid, project_dir))
        return results

    def list_projects(self) -> list[dict[str, Any]]:
        files = self._scan_rollout_files()
        proj_map: dict[str, dict[str, Any]] = {}
        for fp, sid, project_dir in files:
            if project_dir not in proj_map:
                proj_map[project_dir] = {
                    "projectDir": project_dir,
                    "sessions": [],
                }
            proj_map[project_dir]["sessions"].append({
                "id": sid,
                "firstTimestamp": None,
                "lastTimestamp": None,
            })
        result = list(proj_map.values())
        for proj in result:
            sessions = proj["sessions"]
            sessions.sort(key=lambda s: s["id"], reverse=True)
        result.sort(key=lambda p: p["projectDir"])
        return result

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions: list[dict[str, Any]] = []
        for proj in self.list_projects():
            for s in proj.get("sessions", []):
                sessions.append({**s, "projectDir": proj["projectDir"]})
        return sessions

    def raw_to_normalized_events(self, raw_entry: dict[str, Any], session_id: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        typ = raw_entry.get("type", "")
        ts = raw_entry.get("timestamp")
        payload = raw_entry.get("payload", {})

        if typ == "response_item":
            rtype = payload.get("type", "")
            role = payload.get("role", "")
            content_blocks = payload.get("content", [])

            if rtype == "message" and role == "user":
                text = _content_blocks_text(content_blocks, ("input_text", "text"))
                if text:
                    if _is_context_blob(text):
                        events.append(_metadata_event(raw_entry, session_id, "context: environment"))
                        return events
                    events.append({
                        "id": _codex_event_id(raw_entry, session_id, "user_message"),
                        "agent": "codex",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": ts,
                        "role": "user",
                        "kind": "message",
                        "content": text,
                        "summary": _truncate(text),
                        "toolName": None,
                        "toolCallId": None,
                        "parentId": None,
                        "usage": _normalize_usage_helper(None),
                        "raw": raw_entry,
                    })

            elif rtype == "message" and role == "developer":
                full_text = _content_blocks_text(content_blocks, ("output_text", "input_text", "text"))
                summary = "context: developer"
                if full_text and not _is_context_blob(full_text):
                    summary = f"context: developer - {_truncate(full_text, 80)}"
                events.append(_metadata_event(raw_entry, session_id, summary))

            elif rtype == "message" and role == "assistant":
                full_text = _content_blocks_text(content_blocks, ("output_text", "input_text", "text"))
                if full_text:
                    events.append({
                        "id": _codex_event_id(raw_entry, session_id, "assistant_message"),
                        "agent": "codex",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": ts,
                        "role": "assistant",
                        "kind": "message",
                        "content": full_text,
                        "summary": _truncate(full_text),
                        "toolName": None,
                        "toolCallId": None,
                        "parentId": None,
                        "usage": _normalize_usage_helper(None),
                        "raw": raw_entry,
                    })

            elif rtype == "function_call":
                name = payload.get("name", "")
                args = payload.get("arguments", "")
                call_id = payload.get("call_id", "")
                parsed_args = _safe_parse_json(args)
                events.append({
                    "id": _codex_event_id(raw_entry, session_id, f"tool_call:{call_id or name}"),
                    "agent": "codex",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "assistant",
                    "kind": "tool_call",
                    "content": parsed_args,
                    "summary": f"Tool: {name}",
                    "toolName": name,
                    "toolCallId": call_id,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })

            elif rtype == "function_call_output":
                call_id = payload.get("call_id", "")
                output = payload.get("output", "")
                events.append({
                    "id": _codex_event_id(raw_entry, session_id, f"tool_result:{call_id}"),
                    "agent": "codex",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "tool",
                    "kind": "tool_result",
                    "content": output,
                    "summary": _truncate(output),
                    "toolName": None,
                    "toolCallId": call_id,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })

            elif rtype == "reasoning":
                summary_list = payload.get("summary", [])
                summary_text = " ".join(str(s) for s in summary_list) if summary_list else "(reasoning)"
                events.append({
                    "id": _codex_event_id(raw_entry, session_id, "reasoning"),
                    "agent": "codex",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "assistant",
                    "kind": "reasoning",
                    "content": summary_text if summary_list else payload.get("encrypted_content", ""),
                    "summary": _truncate(summary_text),
                    "toolName": None,
                    "toolCallId": None,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })

        elif typ == "event_msg":
            etype = payload.get("type", "")
            if etype == "user_message":
                msg = payload.get("message", "")
                events.append({
                    "id": _codex_event_id(raw_entry, session_id, "event_user_message"),
                    "agent": "codex",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "user",
                    "kind": "message",
                    "content": msg,
                    "summary": _truncate(msg),
                    "toolName": None,
                    "toolCallId": None,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })
            elif etype == "agent_message":
                msg = payload.get("message", "")
                phase = payload.get("phase", "")
                events.append({
                    "id": _codex_event_id(raw_entry, session_id, f"event_agent_message:{phase}"),
                    "agent": "codex",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": "assistant",
                    "kind": "message",
                    "content": msg,
                    "summary": _truncate(msg),
                    "toolName": None,
                    "toolCallId": None,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })
            elif etype == "token_count":
                info = payload.get("info", {})
                total_usage = info.get("total_token_usage") or info.get("last_token_usage") or {}
                if total_usage:
                    events.append({
                        "id": _codex_event_id(raw_entry, session_id, "token_count"),
                        "agent": "codex",
                        "sessionId": session_id,
                        "turnId": None,
                        "timestamp": ts,
                        "role": None,
                        "kind": "metadata",
                        "content": None,
                        "summary": "token usage snapshot",
                        "toolName": None,
                        "toolCallId": None,
                        "parentId": None,
                        "usage": _normalize_usage_helper(total_usage),
                        "raw": raw_entry,
                    })
            elif etype == "patch_apply_end":
                events.append({
                    "id": _codex_event_id(raw_entry, session_id, "patch_apply_end"),
                    "agent": "codex",
                    "sessionId": session_id,
                    "turnId": None,
                    "timestamp": ts,
                    "role": None,
                    "kind": "metadata",
                    "content": payload,
                    "summary": "patch_apply_end",
                    "toolName": None,
                    "toolCallId": None,
                    "parentId": None,
                    "usage": _normalize_usage_helper(None),
                    "raw": raw_entry,
                })

        elif typ == "turn_context":
            cwd = payload.get("cwd", "")
            model = payload.get("model", "")
            events.append({
                "id": _codex_event_id(raw_entry, session_id, "turn_context"),
                "agent": "codex",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": None,
                "kind": "metadata",
                "content": {"cwd": cwd, "model": model},
                "summary": f"turn: {model}",
                "toolName": None,
                "toolCallId": None,
                "parentId": None,
                "usage": _normalize_usage_helper(None),
                "raw": raw_entry,
            })

        elif typ == "session_meta":
            payload_id = payload.get("id", "")
            cwd = payload.get("cwd", "")
            events.append({
                "id": _codex_event_id(raw_entry, session_id, f"session_meta:{payload_id}"),
                "agent": "codex",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": None,
                "kind": "metadata",
                "content": {"sessionId": payload_id, "cwd": cwd},
                "summary": "session meta",
                "toolName": None,
                "toolCallId": None,
                "parentId": None,
                "usage": _normalize_usage_helper(None),
                "raw": raw_entry,
            })

        else:
            events.append({
                "id": _codex_event_id(raw_entry, session_id, f"unknown:{typ}"),
                "agent": "codex",
                "sessionId": session_id,
                "turnId": None,
                "timestamp": ts,
                "role": None,
                "kind": "unknown",
                "content": raw_entry,
                "summary": f"type: {typ}",
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
                if ev["kind"] == "message" and ev["role"] == "user":
                    user_summary = ev.get("summary", "") or ""
                elif ev["kind"] == "message" and ev["role"] == "assistant":
                    assistant_summary = ev.get("summary", "") or ""
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
                "agent": "codex",
                "startedAt": turn_start_ts,
                "endedAt": ended_at,
                "userSummary": user_summary,
                "assistantSummary": assistant_summary,
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

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        files = self._scan_rollout_files()
        for fp, sid, project_dir in files:
            if sid == session_id:
                entries = _read_jsonl(fp)
                events: list[dict[str, Any]] = []
                for e in entries:
                    events.extend(self.raw_to_normalized_events(e, session_id))
                turns = self._build_turns(events)
                sqlite_meta = self._load_sqlite_metadata().get(session_id, {})
                usage: dict[str, Any] = {
                    "scope": "session",
                    "source": "derived",
                    "raw": None,
                }
                if sqlite_meta.get("tokens_used"):
                    usage["totalTokens"] = sqlite_meta["tokens_used"]
                    usage["source"] = "agent_log"
                else:
                    inp_sum: int | None = None
                    outp_sum: int | None = None
                    for ev in events:
                        u = ev.get("usage", {})
                        inp = u.get("inputTokens")
                        outp = u.get("outputTokens")
                        if inp is not None:
                            inp_sum = (inp_sum or 0) + inp
                        if outp is not None:
                            outp_sum = (outp_sum or 0) + outp
                    if inp_sum is not None:
                        usage["inputTokens"] = inp_sum
                    if outp_sum is not None:
                        usage["outputTokens"] = outp_sum
                    if inp_sum is not None and outp_sum is not None:
                        usage["totalTokens"] = inp_sum + outp_sum
                result: dict[str, Any] = {
                    "sessionId": session_id,
                    "projectDir": project_dir,
                    "main": [],
                    "subagents": [],
                    "agent": "codex",
                    "events": events,
                    "turns": turns,
                    "usage": usage,
                }
                if sqlite_meta:
                    result["_metadata"] = sqlite_meta
                return result
        return None
