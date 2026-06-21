"""Viewer HTTP server — serves agent session log data via REST API."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
import urllib.request

from ccwhat.adapters.base import AdapterNotImplementedError, AgentAdapter, SessionRenameError
from ccwhat.adapters.claude import ClaudeAdapter
from ccwhat.session_report import normalize_session_for_report


# ---------------------------------------------------------------------------
# Data loading helpers (kept as thin wrappers for backwards compatibility)
# ---------------------------------------------------------------------------

def get_projects(projects_dir: Path) -> list[dict[str, Any]]:
    """Return list of {projectDir, sessions} for all projects.
    Thin wrapper around ClaudeAdapter for backwards compatibility.
    """
    adapter = ClaudeAdapter(projects_dir)
    return adapter.list_projects()


def get_session(session_id: str, projects_dir: Path) -> dict[str, Any] | None:
    """Find session by ID across all project dirs.
    Thin wrapper around ClaudeAdapter for backwards compatibility.
    """
    adapter = ClaudeAdapter(projects_dir)
    return adapter.load_session(session_id)


# ---------------------------------------------------------------------------
# HTTP record helpers (unchanged)
# ---------------------------------------------------------------------------

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


def get_message_http(
    session_id: str,
    message_id: str,
    projects_dir: Path,
    logs_dir: Path,
) -> list[dict[str, Any]] | None:
    """Find HTTP records matching an assistant message ID (msg_bdrk_xxx)."""
    session_data = get_session(session_id, projects_dir)
    if session_data is None:
        return None
    if not logs_dir.is_dir():
        return []
    matches = []
    for parsed_path in sorted(logs_dir.glob("*_parsed.jsonl")):
        for record in _read_jsonl(parsed_path):
            if record.get("claude_session_id") != session_id:
                continue
            rec_msg_id = record.get("response_json", {}).get("message", {}).get("id")
            if rec_msg_id == message_id:
                matches.append(record)
    matches.sort(key=lambda r: r.get("timestamp", ""))
    return matches


def get_message_source(
    session_id: str,
    message_id: str,
    projects_dir: Path,
) -> dict[str, Any] | None:
    """Find the source (main or subagent) of an assistant message by message.id."""
    session_data = get_session(session_id, projects_dir)
    if session_data is None:
        return None
    for entry in session_data.get("main", []):
        if entry.get("type") == "assistant" and entry.get("message", {}).get("id") == message_id:
            return {"source": "main"}
    for sa in session_data.get("subagents", []):
        for entry in sa.get("entries", []):
            if entry.get("type") == "assistant" and entry.get("message", {}).get("id") == message_id:
                return {"source": "subagent", "agentId": sa.get("agentId", "")}
    return {}


def get_logs(
    logs_dir: Path,
    session_filter: str | None = None,
) -> dict[str, Any]:
    """Return all parsed log records from *_parsed.jsonl files."""
    if not logs_dir.is_dir():
        return {"records": [], "sessions": []}
    all_records: list[dict] = []
    for parsed_path in sorted(logs_dir.glob("*_parsed.jsonl")):
        all_records.extend(_read_jsonl(parsed_path))
    sessions = sorted({r.get("claude_session_id", "") for r in all_records if r.get("claude_session_id")})
    if session_filter:
        all_records = [r for r in all_records if r.get("claude_session_id") == session_filter]
    all_records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return {"records": all_records, "sessions": sessions}


def _read_auth_token_from_config() -> str | None:
    """Read AUTHORIZATION token from ~/.config/mcopilot-cli/.config.yaml."""
    config_path = Path.home() / ".config" / "mcopilot-cli" / ".config.yaml"
    try:
        for line in config_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("AUTHORIZATION:"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def _parse_x_client_token_from_env() -> str | None:
    """Parse X-Client-Token from ANTHROPIC_CUSTOM_HEADERS environment variable.

    ANTHROPIC_CUSTOM_HEADERS format:
        X-Repo-Url: xxx
        X-Branch: xxx
        X-Client-Token: <token-value>
        ...
    """
    custom_headers = os.environ.get("ANTHROPIC_CUSTOM_HEADERS", "")
    for line in custom_headers.split("\n"):
        line = line.strip()
        if line.startswith("X-Client-Token:"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()
    return None


def get_req_resp_sessions(logs_dir: Path) -> dict[str, Any]:
    """Return all session IDs and their available date files under logs_dir."""
    if not logs_dir.is_dir():
        return {"sessions": []}
    sessions = []
    for session_dir in sorted(logs_dir.iterdir()):
        if not session_dir.is_dir():
            continue
        dates = sorted(
            p.stem for p in session_dir.glob("*.jsonl")
            if not p.name.endswith("_parsed.jsonl")
        )
        if dates:
            sessions.append({"id": session_dir.name, "dates": dates})
    return {"sessions": sessions}


def _extract_sse_message_id(sse_events: list[str]) -> str | None:
    """Parse SSE events and return message.id from message_start event."""
    for ev in sse_events:
        for line in ev.split("\n"):
            if not line.startswith("data:"):
                continue
            raw = line[len("data:"):].strip()
            try:
                d = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if d.get("type") == "message_start":
                return d.get("message", {}).get("id")
    return None


def get_req_resp_records(logs_dir: Path, session_id: str, date: str) -> list[dict]:
    """Return raw records from logs_dir/<session_id>/<date>.jsonl."""
    jsonl_path = logs_dir / session_id / f"{date}.jsonl"
    if not jsonl_path.exists():
        return []
    records = _read_jsonl(jsonl_path)
    for r in records:
        if r.get("is_sse") and r.get("sse_events"):
            r["_message_id"] = _extract_sse_message_id(r["sse_events"])
        else:
            r["_message_id"] = None
    return records


# ---------------------------------------------------------------------------
# Recording status API
# ---------------------------------------------------------------------------

def get_recording_status(logs_dir: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Return recording config and health status for the viewer status panel."""
    try:
        from ccwhat.config import DEFAULT_CONFIG_PATH, load_config
        cfg_path = config_path or DEFAULT_CONFIG_PATH
        cfg = load_config(cfg_path)
    except Exception:
        cfg = None
        cfg_path = None
    latest_ts: str | None = None
    if logs_dir.is_dir():
        jsonl_files = sorted(logs_dir.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        for jf in jsonl_files[:1]:
            latest_ts = jf.stat().st_mtime.__str__()
    if cfg is None:
        return {
            "configValid": False,
            "configPath": str(cfg_path) if cfg_path else None,
            "domains": [],
            "paths": [],
            "rawLogDir": str(logs_dir),
            "latestRawLogTimestamp": latest_ts,
            "redactionSummary": "Default header redaction active",
            "maxBodyBytes": None,
            "preset": None,
        }
    return {
        "configValid": cfg.is_valid_for_recording(),
        "configPath": str(cfg_path),
        "domains": cfg.effective_domains(),
        "paths": cfg.effective_paths(),
        "rawLogDir": str(logs_dir),
        "latestRawLogTimestamp": latest_ts,
        "redactionSummary": f"{len(cfg.redact_headers)} sensitive headers redacted by default",
        "maxBodyBytes": cfg.max_body_bytes,
        "preset": cfg.preset,
    }


# ---------------------------------------------------------------------------
# Scoped search helpers
# ---------------------------------------------------------------------------

SEARCH_SCOPES = {"current_session", "current_project", "all_projects"}
DEFAULT_SEARCH_LIMIT = 50
MAX_SEARCH_LIMIT = 200


def _plain_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_plain_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_plain_text(v)}" for k, v in value.items())
    return str(value)


def _short_snippet(text: Any, query: str, *, max_len: int = 110) -> str:
    clean = re.sub(r"\s+", " ", _plain_text(text)).strip()
    if len(clean) <= max_len:
        return clean
    pos = clean.lower().find(query.lower())
    if pos < 0:
        return clean[:max_len - 1] + "…"
    start = max(0, pos - max_len // 3)
    end = min(len(clean), start + max_len)
    start = max(0, end - max_len)
    prefix = "…" if start else ""
    suffix = "…" if end < len(clean) else ""
    return prefix + clean[start:end].strip() + suffix


def _search_result_key(result: dict[str, Any]) -> tuple[str, str, str]:
    typ = str(result.get("type") or "")
    session_id = str(result.get("sessionId") or "")
    if typ == "task":
        return (typ, session_id, str(result.get("taskId") or ""))
    if typ == "session":
        return (typ, session_id, "")
    snippet = re.sub(r"\s+", " ", str(result.get("snippet") or "")).strip().lower()
    return (typ, session_id, snippet[:100])


def _dedupe_search_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for result in results:
        key = _search_result_key(result)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(result)
    return deduped


def _field_matches(fields: dict[str, Any], query: str) -> list[str]:
    q = query.lower()
    return [name for name, value in fields.items() if q in _plain_text(value).lower()]


def _session_info_id(session_info: Any) -> str:
    if isinstance(session_info, dict):
        return str(session_info.get("id") or session_info.get("sessionId") or "")
    return str(session_info or "")


def _iter_session_candidates(
    projects: list[dict[str, Any]],
    *,
    scope: str,
    project_dir: str,
    session_id: str,
) -> tuple[list[dict[str, Any]], str | None]:
    candidates: list[dict[str, Any]] = []
    for project in projects:
        pdir = str(project.get("projectDir") or "")
        if scope == "current_project" and pdir != project_dir:
            continue
        for info in project.get("sessions", []) or []:
            sid = _session_info_id(info)
            if not sid:
                continue
            if scope == "current_session" and sid != session_id:
                continue
            candidates.append({
                "sessionId": sid,
                "projectDir": pdir,
                "session": info if isinstance(info, dict) else {"id": sid},
            })
    if scope == "current_session" and session_id and not candidates:
        return [{"sessionId": session_id, "projectDir": project_dir, "session": {"id": session_id}}], None
    if scope == "current_project" and project_dir and not any(str(p.get("projectDir") or "") == project_dir for p in projects):
        return [], f"project not found: {project_dir}"
    return candidates, None


def _search_session_metadata(candidate: dict[str, Any], query: str) -> list[dict[str, Any]]:
    info = candidate.get("session") or {}
    fields = {
        "sessionId": candidate["sessionId"],
        "projectDir": candidate["projectDir"],
        "title": info.get("title") if isinstance(info, dict) else "",
        "displayName": info.get("displayName") if isinstance(info, dict) else "",
        "firstTimestamp": info.get("firstTimestamp") if isinstance(info, dict) else "",
        "lastTimestamp": info.get("lastTimestamp") if isinstance(info, dict) else "",
    }
    matched = _field_matches(fields, query)
    if not matched:
        return []
    return [{
        "type": "session",
        "sessionId": candidate["sessionId"],
        "projectDir": candidate["projectDir"],
        "displayName": fields.get("displayName") or "",
        "title": fields.get("title") or "",
        "matchedFields": matched,
        "snippet": _short_snippet(" ".join(_plain_text(fields[name]) for name in matched), query),
        "timestamp": fields.get("lastTimestamp") or fields.get("firstTimestamp") or "",
    }]


def _search_session_content(
    session_data: dict[str, Any],
    project_dir: str,
    query: str,
    session_info: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    report_session = normalize_session_for_report(session_data)
    session_id = str(session_data.get("sessionId") or report_session.session_id or "")
    info = session_info or {}
    display_name = str(session_data.get("displayName") or info.get("displayName") or "")
    title = str(session_data.get("title") or info.get("title") or "")
    event_to_turn: dict[str, str] = {}
    for turn in report_session.turns:
        for event_id in turn.event_ids:
            event_to_turn[event_id] = turn.turn_id
    for event in report_session.events:
        fields = {
            "content": event.content,
            "summary": event.summary,
            "toolName": event.tool_name,
            "role": event.role,
            "kind": event.kind,
        }
        matched = _field_matches(fields, query)
        if not matched:
            continue
        results.append({
            "type": "event",
            "sessionId": session_id,
            "projectDir": project_dir,
            "displayName": display_name,
            "title": title,
            "eventId": event.event_id,
            "turnId": event_to_turn.get(event.event_id),
            "timestamp": event.timestamp or "",
            "matchedFields": matched,
            "snippet": _short_snippet(" ".join(_plain_text(fields[name]) for name in matched), query),
        })
    for turn in report_session.turns:
        fields = {
            "userSummary": turn.user_summary,
            "assistantSummary": turn.assistant_summary,
        }
        matched = _field_matches(fields, query)
        if not matched:
            continue
        results.append({
            "type": "turn",
            "sessionId": session_id,
            "projectDir": project_dir,
            "displayName": display_name,
            "title": title,
            "turnId": turn.turn_id,
            "eventId": (turn.event_ids or [None])[0],
            "timestamp": turn.started_at or turn.ended_at or "",
            "matchedFields": matched,
            "snippet": _short_snippet(" ".join(_plain_text(fields[name]) for name in matched), query),
        })
    return results


def _dataset_registry_task_results(
    *,
    registry_root: Path | None,
    candidate_session_ids: set[str],
    query: str,
) -> list[dict[str, Any]]:
    from ccwhat.task_dataset import default_dataset_registry_root

    root = (registry_root or default_dataset_registry_root()).expanduser()
    if not root.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for dataset_dir in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
        if not dataset_dir.is_dir():
            continue
        manifest_path = dataset_dir / "manifest.json"
        dataset_path = dataset_dir / "dataset.jsonl"
        if not manifest_path.is_file() or not dataset_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            project_dir = str((manifest.get("session") or {}).get("project_dir") or "")
            for raw_line in dataset_path.read_text(encoding="utf-8").splitlines():
                if not raw_line.strip():
                    continue
                row = json.loads(raw_line)
                metadata = row.get("metadata") or {}
                session_id = str(metadata.get("session_id") or "")
                if session_id not in candidate_session_ids:
                    continue
                trace_path = str(metadata.get("trace_path") or "")
                trace = {}
                if trace_path:
                    trace_file = dataset_dir / trace_path
                    if trace_file.is_file():
                        trace = json.loads(trace_file.read_text(encoding="utf-8"))
                fields = {
                    "taskId": row.get("id"),
                    "title": (row.get("input") or {}).get("instruction"),
                    "taskType": metadata.get("task_type"),
                    "status": metadata.get("status"),
                    "startEventId": metadata.get("start_event_id"),
                    "endEventId": metadata.get("end_event_id"),
                    "commands": trace.get("commands"),
                    "testCommands": trace.get("test_commands"),
                    "filesRead": (trace.get("files") or {}).get("read"),
                    "filesChanged": (trace.get("files") or {}).get("changed"),
                    "errors": trace.get("errors"),
                    "finalClaim": trace.get("final_claim"),
                }
                matched = _field_matches(fields, query)
                if not matched:
                    continue
                results.append({
                    "type": "task",
                    "sessionId": session_id,
                    "projectDir": project_dir,
                    "taskId": str(row.get("id") or ""),
                    "title": _plain_text(fields["title"])[:120],
                    "taskType": str(metadata.get("task_type") or ""),
                    "eventId": str(metadata.get("start_event_id") or ""),
                    "matchedFields": matched,
                    "snippet": _short_snippet(" ".join(_plain_text(fields[name]) for name in matched), query),
                    "timestamp": str((manifest.get("created_at") or "")),
                    "source": "dataset",
                    "datasetId": dataset_dir.name,
                })
        except (OSError, json.JSONDecodeError):
            continue
    return results


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

def _make_handler(
    projects_dir: Path,
    logs_dir: Path,
    config_path: Path | None = None,
    analyzer_cmd: list[str] | tuple[str, ...] | None = None,
    adapter: AgentAdapter | None = None,
    analyzer_agent: str | None = None,
    analyzer_timeout: int | None = None,
    dataset_registry_root: Path | None = None,
):
    viewer_dir = Path(__file__).parent
    _adapter = adapter
    _analyzer_agent = analyzer_agent
    _analyzer_timeout = analyzer_timeout
    report_store: dict[str, dict] = {}
    replay_store: dict[str, dict] = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            pass

        def _send_file(self, file_path: Path) -> None:
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: Any, status: int = 200) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, Any] | None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return None
            if length <= 0:
                return {}
            try:
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None
            return data if isinstance(data, dict) else None

        def _send_binary(self, data: bytes, content_type: str, filename: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        def _handle_replay_create_session(self) -> None:
            """Create a new replay session and store it in server memory."""
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"ok": False, "error": "invalid JSON body"}, 400)
                return

            record = payload.get("record", {})
            req_json = payload.get("reqJson", {})
            original_text = payload.get("originalText", "")
            record_key = payload.get("recordKey", "")

            if not record or not req_json:
                self._send_json({"ok": False, "error": "missing record or reqJson"}, 400)
                return

            session_id = uuid.uuid4().hex
            session_data = {
                "record": record,
                "reqJson": req_json,
                "originalText": original_text,
                "editedText": original_text,
                "isLoading": False,
                "result": None,
                "error": None,
            }
            replay_store[session_id] = session_data
            if record_key:
                replay_store[f"rk:{record_key}"] = session_data

            self._send_json({"ok": True, "sessionId": session_id})

        def _handle_replay_send(self) -> None:
            """Send replay request using stored session."""
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"ok": False, "error": "invalid JSON body"}, 400)
                return

            session_id = payload.get("sessionId", "")
            edited_text = payload.get("editedText")

            if not session_id or session_id not in replay_store:
                self._send_json({"ok": False, "error": "session not found"}, 404)
                return

            session = replay_store[session_id]
            should_edit_request = edited_text is not None
            if should_edit_request:
                session["editedText"] = edited_text

            session["isLoading"] = True
            req_body = json.loads(json.dumps(session["reqJson"]))
            msgs = req_body.get("messages", [])

            if should_edit_request and msgs:
                last_msg = msgs[-1]
                content = last_msg.get("content", "")
                if isinstance(content, str):
                    last_msg["content"] = session["editedText"]
                elif isinstance(content, list):
                    for block in content:
                        if block.get("type") == "text":
                            block["text"] = session["editedText"]
                            break
                    else:
                        for block in content:
                            if block.get("type") != "tool_result":
                                continue
                            tool_content = block.get("content")
                            if isinstance(tool_content, str):
                                block["content"] = session["editedText"]
                            elif isinstance(tool_content, list):
                                for item in tool_content:
                                    if item.get("type") == "text":
                                        item["text"] = session["editedText"]
                                        break
                                else:
                                    block["content"] = session["editedText"]
                            else:
                                block["content"] = session["editedText"]
                            break
                        else:
                            last_msg["content"] = session["editedText"]
                    if not any(b.get("type") in {"text", "tool_result"} for b in content):
                        last_msg["content"] = session["editedText"]

            api_url = os.environ.get("CLAUDE_API_URL", "https://mcli.sankuai.com/v1/messages")
            if "?" not in api_url:
                api_url += "?beta=true"

            record = session["record"]
            orig_headers = record.get("request", {}).get("headers", {})
            hop_by_hop = {"host", "content-length", "accept-encoding", "connection", "transfer-encoding", "keep-alive"}
            headers = {k: v for k, v in orig_headers.items() if k.lower() not in hop_by_hop}

            fresh_token = _parse_x_client_token_from_env()
            if fresh_token:
                headers["X-Client-Token"] = fresh_token

            auth_token = _read_auth_token_from_config() or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            req_body["stream"] = False
            headers["Accept"] = "application/json"

            try:
                data = json.dumps(req_body).encode("utf-8")
                req = urllib.request.Request(api_url, data=data, headers=headers, method="POST")
                response = urllib.request.urlopen(req, timeout=600)
                status = response.getcode()
                if status != 200:
                    error_body = response.read().decode("utf-8", errors="replace")[:500]
                    response.close()
                    raise Exception(f"API returned status {status}: {error_body}")
                response_data = response.read()
                response.close()
                result = json.loads(response_data)
                session["result"] = result
                session["isLoading"] = False
                self._send_json({"ok": True, "result": result})
            except Exception as e:
                session["isLoading"] = False
                session["error"] = str(e)
                self._send_json({"ok": False, "error": str(e)}, 500)

        def _get_sessions_data(self) -> list[dict[str, Any]]:
            if _adapter is not None:
                return _adapter.list_projects()
            return get_projects(projects_dir)

        def _get_session_data(self, session_id: str) -> dict[str, Any] | None:
            if _adapter is not None:
                return _adapter.load_session(session_id)
            return get_session(session_id, projects_dir)

        def _adapter_agent(self) -> str | None:
            if _adapter is not None:
                return _adapter.name
            return None

        def _handle_search(self, query_string: str) -> None:
            params = parse_qs(query_string)
            raw_query = params.get("q", [""])[0]
            normalized_query = re.sub(r"\s+", " ", raw_query).strip()
            if len(normalized_query) < 2:
                self._send_json({"ok": False, "error": "query must be at least 2 characters"}, 400)
                return

            scope = params.get("scope", ["current_session"])[0] or "current_session"
            if scope not in SEARCH_SCOPES:
                self._send_json({"ok": False, "error": "invalid search scope"}, 400)
                return

            project_dir = params.get("project", [""])[0].strip()
            session_id = params.get("session", [""])[0].strip()
            if scope == "current_session":
                if not re.fullmatch(r"[0-9a-zA-Z_-]{20,64}", session_id):
                    self._send_json({"ok": False, "error": "current_session scope requires a valid session"}, 400)
                    return
            elif scope == "current_project" and not project_dir:
                self._send_json({"ok": False, "error": "current_project scope requires project"}, 400)
                return

            try:
                limit = int(params.get("limit", [str(DEFAULT_SEARCH_LIMIT)])[0] or DEFAULT_SEARCH_LIMIT)
            except ValueError:
                self._send_json({"ok": False, "error": "limit must be a number"}, 400)
                return
            if limit < 1:
                self._send_json({"ok": False, "error": "limit must be at least 1"}, 400)
                return
            limit = min(limit, MAX_SEARCH_LIMIT)

            try:
                projects = self._get_sessions_data()
            except AdapterNotImplementedError as exc:
                self._send_json({"ok": False, "error": str(exc), "agent": self._adapter_agent() or "claude"}, 501)
                return

            candidates, source_error = _iter_session_candidates(
                projects,
                scope=scope,
                project_dir=project_dir,
                session_id=session_id,
            )
            if source_error:
                self._send_json({"ok": False, "error": source_error}, 404)
                return
            if not candidates:
                self._send_json({
                    "ok": True,
                    "query": normalized_query,
                    "scope": scope,
                    "results": [],
                    "truncated": False,
                    "warnings": [{"message": "no searchable sessions found"}],
                })
                return

            results: list[dict[str, Any]] = []
            warnings: list[dict[str, str]] = []
            searchable_session_ids: set[str] = set()

            for candidate in candidates:
                if len(results) > limit:
                    break
                results.extend(_search_session_metadata(candidate, normalized_query))
                sid = candidate["sessionId"]
                try:
                    session_data = self._get_session_data(sid)
                    if session_data is None:
                        warnings.append({"sessionId": sid, "projectDir": candidate["projectDir"], "message": "session not found"})
                        continue
                    searchable_session_ids.add(sid)
                    results.extend(_search_session_content(
                        session_data,
                        candidate["projectDir"],
                        normalized_query,
                        session_info=candidate.get("session") if isinstance(candidate.get("session"), dict) else None,
                    ))
                except Exception as exc:
                    warnings.append({"sessionId": sid, "projectDir": candidate["projectDir"], "message": str(exc)})

            searchable_session_ids.update(candidate["sessionId"] for candidate in candidates)
            results.extend(_dataset_registry_task_results(
                registry_root=dataset_registry_root,
                candidate_session_ids=searchable_session_ids,
                query=normalized_query,
            ))

            results = _dedupe_search_results(results)
            results.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
            truncated = len(results) > limit
            self._send_json({
                "ok": True,
                "query": normalized_query,
                "scope": scope,
                "results": results[:limit],
                "truncated": truncated,
                "warnings": warnings,
            })

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_POST(self) -> None:
            total_started = time.monotonic()
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            # Handle replay endpoints (no session validation required)
            if path == "/api/replay/session":
                self._handle_replay_create_session()
                return
            if path == "/api/replay/send":
                self._handle_replay_send()
                return

            # ── POST /api/session/<sessionId>/rename ──────────────────────
            rename_prefix = "/api/session/"
            rename_suffix = "/rename"
            if path.startswith(rename_prefix) and path.endswith(rename_suffix):
                session_id = path[len(rename_prefix):-len(rename_suffix)]
                if not re.fullmatch(r"[0-9a-zA-Z_-]{20,64}", session_id):
                    self._send_json({"ok": False, "error": "invalid session id", "code": "invalid_title"}, 400)
                    return
                payload = self._read_json_body()
                if payload is None:
                    self._send_json({"ok": False, "error": "invalid JSON body", "code": "invalid_title"}, 400)
                    return
                raw_title = payload.get("title", "")
                title = str(raw_title).strip() if raw_title else ""
                if not title:
                    self._send_json({"ok": False, "error": "title is required and must not be empty", "code": "invalid_title"}, 400)
                    return

                adapter = _adapter
                if adapter is None:
                    self._send_json({"ok": False, "error": "rename not supported for this agent", "code": "rename_not_supported"}, 501)
                    return

                if not adapter.can_rename_session:
                    self._send_json({"ok": False, "error": "rename not supported for this agent", "code": "rename_not_supported"}, 501)
                    return

                try:
                    result = adapter.rename_session(session_id, title)
                except SessionRenameError as exc:
                    status_map = {
                        "invalid_title": 400,
                        "session_not_found": 404,
                        "rename_not_supported": 501,
                        "native_title_unavailable": 500,
                        "native_title_write_failed": 500,
                    }
                    http_status = status_map.get(exc.code, 500)
                    self._send_json({"ok": False, "error": exc.message, "code": exc.code}, http_status)
                    return

                self._send_json({
                    "ok": True,
                    "agent": adapter.name,
                    "sessionId": session_id,
                    "title": result["title"],
                    "displayName": result["displayName"],
                    "canRenameSession": result["canRenameSession"],
                })
                return

            if path not in ("/api/analyze", "/api/task-segments", "/api/save-task-dataset"):
                self._send_json({"ok": False, "error": "not found"}, 404)
                return
            payload = self._read_json_body()
            if payload is None:
                self._send_json({"ok": False, "error": "invalid JSON body"}, 400)
                return
            session_id = str(payload.get("sessionId", "")).strip()
            if not re.fullmatch(r"[0-9a-zA-Z_-]{20,64}", session_id):
                self._send_json({"ok": False, "error": "invalid session id"}, 400)
                return
            mode = str(payload.get("mode", "")).strip()
            custom_prompt = str(payload.get("customPrompt", "")).strip()

            session = self._get_session_data(session_id)
            if session is None:
                self._send_json({"ok": False, "error": "session not found"}, 404)
                return

            if path == "/api/save-task-dataset":
                from ccwhat.task_dataset import DatasetRegistryError, save_task_dataset_from_request
                try:
                    saved = save_task_dataset_from_request(
                        payload=payload,
                        session=session,
                        registry_root=dataset_registry_root,
                    )
                except DatasetRegistryError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, exc.status)
                    return
                self._send_json({
                    "ok": True,
                    "datasetId": saved.dataset_id,
                    "datasetPath": str(saved.dataset_path),
                    "downloadUrl": saved.download_url,
                })
                return

            # ── /api/task-segments ─────────────────────────────────────────
            if path == "/api/task-segments":
                from ccwhat.task_segments import segment_session
                started = time.monotonic()
                result = segment_session(session)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                tasks_json = []
                for idx, t in enumerate(result.tasks, 1):
                    tasks_json.append({
                        "taskId": t.task_id,
                        "title": f"任务 {idx}",
                        "taskType": t.task_type,
                        "status": t.status,
                        "startEventId": t.start_event_id,
                        "endEventId": t.end_event_id,
                        "isAmbiguous": t.is_ambiguous,
                        "finalClaim": t.final_claim,
                        "boundaryReasons": t.boundary_reasons,
                        "evidence": {
                            "filesRead": t.evidence.files_read,
                            "filesChanged": t.evidence.files_changed,
                            "commands": t.evidence.commands,
                            "testCommands": t.evidence.test_commands,
                            "errors": t.evidence.errors,
                            "skills": t.evidence.skills,
                            "subagentIds": t.evidence.subagent_ids,
                            "finalClaims": t.evidence.final_claims,
                            "todosUser": t.evidence.todos_user,
                        },
                        "fileWeights": t.file_weights,
                    })
                self._send_json({
                    "ok": True,
                    "sessionId": result.session_id,
                    "summary": result.summary,
                    "tasks": tasks_json,
                    "isAmbiguous": result.is_ambiguous,
                    "elapsedMs": elapsed_ms,
                    "debugBoundaries": [
                        {"eventId": b.event_id, "score": b.score,
                         "shouldSplit": b.should_split, "reasons": b.reasons}
                        for b in result.debug_boundaries
                    ],
                })
                return

            if mode in ("yuanxi", "generic"):
                # New HTML report pipeline (session_report module)
                from ccwhat.session_report import build_generic_html_report, build_html_session_report
                report_session = normalize_session_for_report(session)
                report_started = time.monotonic()
                effective_agent = _analyzer_agent or self._adapter_agent() or report_session.primary_agent_type or "claude"
                if mode == "generic":
                    result = build_generic_html_report(
                        session,
                        custom_prompt=custom_prompt,
                        analyzer_cmd=analyzer_cmd,
                        analyzer_agent=effective_agent,
                        analyzer_timeout=_analyzer_timeout,
                    )
                else:
                    result = build_html_session_report(
                        session,
                        custom_prompt=custom_prompt,
                        analyzer_cmd=analyzer_cmd,
                        analyzer_agent=effective_agent,
                        analyzer_timeout=_analyzer_timeout,
                    )
                report_id = uuid.uuid4().hex
                report_html = str(result.get("reportHtml") or "")
                report_store[report_id] = {"html": report_html, "mode": mode, "sessionId": session_id}
                report_url = f"/api/analysis-report/{report_id}"
                export_url = f"/api/analysis-report/{report_id}/export"
                from ccwhat.analyzers.registry import get as _get_analyzer_spec
                analyzer_spec = _get_analyzer_spec(effective_agent)
                self._send_json({
                    "ok": True,
                    "reportType": result["reportType"],
                    "reportMode": result.get("reportMode", mode),
                    "reportUrl": report_url,
                    "exportUrl": export_url,
                    "summary": result.get("summary"),
                    "elapsedMs": result["elapsedMs"],
                    "truncated": bool((result.get("compression") or {}).get("omittedEvents")),
                    "compression": result.get("compression"),
                    "diagnosisStatus": result.get("diagnosisStatus"),
                    "llmStatus": result.get("llmStatus"),
                    "buildMs": int((time.monotonic() - report_started) * 1000),
                    "totalMs": int((time.monotonic() - total_started) * 1000),
                    "analyzerAgent": effective_agent,
                    "analyzerOutputMode": analyzer_spec.output_mode if analyzer_spec else "unknown",
                    "experimental": analyzer_spec.experimental if analyzer_spec else False,
                })
            else:
                self._send_json({"ok": False, "error": "mode is required (yuanxi or generic)", "code": "invalid_mode"}, 400)
                return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            query = parsed.query
            _static: dict[str, str] = {
                "": "index.html",
                "/index.html": "index.html",
                "/claude-log.html": "claude-log.html",
                "/req-resp.html": "req-resp.html",
            }
            if path in _static:
                self._send_file(viewer_dir / _static[path])
                return
            if path == "/api/replay/status":
                from urllib.parse import parse_qs
                params = parse_qs(query)
                record_key = params.get("recordKey", [""])[0]
                if not record_key:
                    self._send_json({"error": "missing recordKey parameter"}, 400)
                    return
                rk_key = f"rk:{record_key}"
                if rk_key in replay_store:
                    session = replay_store[rk_key]
                    self._send_json({
                        "ok": True,
                        "hasReplay": True,
                        "originalText": session["originalText"],
                        "editedText": session["editedText"],
                        "result": session.get("result"),
                        "isLoading": session.get("isLoading", False),
                        "error": session.get("error"),
                    })
                else:
                    self._send_json({"ok": True, "hasReplay": False})
                return
            if path == "/api/viewer/status":
                self._send_json({
                    "ok": True,
                    "agent": self._adapter_agent() or "claude",
                    "projectsDir": str(projects_dir),
                })
            elif path == "/api/recording/status":
                self._send_json(get_recording_status(logs_dir, config_path))
            elif path == "/api/search":
                self._handle_search(query)
            elif path == "/api/projects":
                try:
                    projects = self._get_sessions_data()
                    for proj in projects:
                        proj["agent"] = self._adapter_agent() or "claude"
                    self._send_json(projects)
                except AdapterNotImplementedError as exc:
                    self._send_json({"error": str(exc), "agent": self._adapter_agent() or "claude"}, 501)
            elif path.startswith("/api/session/"):
                rest = path[len("/api/session/"):]
                # Skip sub-routes like /api/session/<id>/rename (handled by POST)
                if "/" in rest:
                    self._send_json({"error": "not found"}, 404)
                    return
                session_id = rest
                if not re.fullmatch(r"[0-9a-zA-Z_-]{20,64}", session_id):
                    self._send_json({"error": "invalid session id"}, 400)
                    return
                try:
                    data = self._get_session_data(session_id)
                    if data is None:
                        self._send_json({"error": "session not found"}, 404)
                    else:
                        report_session = normalize_session_for_report(data)
                        data["agent"] = data.get("agent") or report_session.primary_agent_type or self._adapter_agent() or "claude"
                        data["events"] = [
                            {
                                "id": event.event_id,
                                "agentId": event.agent_id,
                                "timestamp": event.timestamp,
                                "role": event.role,
                                "kind": event.kind,
                                "content": event.content,
                                "summary": event.summary,
                                "toolName": event.tool_name,
                                "toolCallId": event.tool_call_id,
                                "parentId": event.parent_event_id,
                                "usage": event.usage,
                                "raw": event.raw,
                            }
                            for event in report_session.events
                        ]
                        data["turns"] = [
                            {
                                "id": turn.turn_id,
                                "agentId": turn.agent_id,
                                "startedAt": turn.started_at,
                                "endedAt": turn.ended_at,
                                "userSummary": turn.user_summary,
                                "assistantSummary": turn.assistant_summary,
                                "events": [{"id": event_id} for event_id in turn.event_ids],
                                "usage": turn.usage,
                            }
                            for turn in report_session.turns
                        ]
                        self._send_json(data)
                except AdapterNotImplementedError as exc:
                    self._send_json({"error": str(exc), "agent": self._adapter_agent() or "claude"}, 501)
            elif path == "/api/logs":
                from urllib.parse import parse_qs
                params = parse_qs(query)
                session_filter = params.get("session", [None])[0]
                self._send_json(get_logs(logs_dir, session_filter))
            elif path.startswith("/api/message-http/"):
                rest = path[len("/api/message-http/"):]
                parts = rest.split("/", 1)
                if len(parts) != 2:
                    self._send_json({"error": "invalid path"}, 400)
                    return
                session_id, message_id = parts
                if not re.fullmatch(r"[0-9a-f-]{36}", session_id):
                    self._send_json({"error": "invalid session id"}, 400)
                    return
                records = get_message_http(session_id, message_id, projects_dir, logs_dir)
                if records is None:
                    self._send_json({"error": "message not found"}, 404)
                else:
                    self._send_json({"records": records})
            elif path.startswith("/api/message-source/"):
                rest = path[len("/api/message-source/"):]
                parts = rest.split("/", 1)
                if len(parts) != 2:
                    self._send_json({"error": "invalid path"}, 400)
                    return
                session_id, message_id = parts
                if not re.fullmatch(r"[0-9a-f-]{36}", session_id):
                    self._send_json({"error": "invalid session id"}, 400)
                    return
                result = get_message_source(session_id, message_id, projects_dir)
                if result is None:
                    self._send_json({"error": "session not found"}, 404)
                else:
                    self._send_json(result)
            elif path == "/api/req-resp/sessions":
                self._send_json(get_req_resp_sessions(logs_dir))
            elif path == "/api/req-resp/records":
                from urllib.parse import parse_qs
                params = parse_qs(query)
                session_id = params.get("session", [""])[0]
                date = params.get("date", [""])[0]
                if not session_id or not date:
                    self._send_json({"error": "session and date are required"}, 400)
                    return
                records = get_req_resp_records(logs_dir, session_id, date)
                self._send_json({"records": records})
            elif path == "/api/export":
                from urllib.parse import parse_qs
                from ccwhat.exporter import build_tar_gz_bytes, default_filename
                params = parse_qs(query)
                raw_sessions = params.get("sessions", [""])[0]
                session_ids = [s.strip() for s in raw_sessions.split(",") if s.strip()]
                if not session_ids:
                    self._send_json({"error": "sessions parameter is required"}, 400)
                    return
                invalid = [s for s in session_ids if not re.fullmatch(r"[0-9a-f-]{36}", s)]
                if invalid:
                    self._send_json({"error": f"invalid session id(s): {', '.join(invalid)}"}, 400)
                    return
                first_session = session_ids[0] if len(session_ids) == 1 else None
                filename = params.get("filename", [""])[0].strip() or default_filename(first_session, len(session_ids))
                filename = Path(filename).name.replace('"', "_").replace("\r", "_").replace("\n", "_")
                raw_include = params.get("include", ["claudeLogs,subagentLogs,reqResp"])[0]
                included_keys = {k.strip() for k in raw_include.split(",")}
                content_options = {
                    "claudeLogs": "claudeLogs" in included_keys,
                    "subagentLogs": "subagentLogs" in included_keys,
                    "reqResp": "reqResp" in included_keys,
                }
                req_resp_dates: dict[str, list[str]] = {
                    s["id"]: s["dates"]
                    for s in get_req_resp_sessions(logs_dir)["sessions"]
                }
                try:
                    data, _ = build_tar_gz_bytes(
                        session_ids, projects_dir, logs_dir, req_resp_dates, get_session,
                        content_options,
                    )
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, 404)
                    return
                self._send_binary(data, "application/gzip", filename)
            elif path.startswith("/api/task-datasets/") and path.endswith("/download"):
                dataset_id = path[len("/api/task-datasets/"):-len("/download")].strip("/")
                from ccwhat.task_dataset import DatasetRegistryError, build_dataset_tar_gz
                try:
                    data, filename = build_dataset_tar_gz(
                        dataset_id=dataset_id,
                        registry_root=dataset_registry_root,
                    )
                except DatasetRegistryError as exc:
                    self._send_json({"ok": False, "error": str(exc)}, exc.status)
                    return
                self._send_binary(data, "application/gzip", filename)
            elif path.startswith("/api/analysis-report/") and path.endswith("/export"):
                report_id = path[len("/api/analysis-report/"):-len("/export")]
                entry = report_store.get(report_id)
                if entry is None:
                    self._send_json({"error": "report not found or expired"}, 404)
                else:
                    report_mode = entry.get("mode", "report")
                    filename = f"session-report-{report_mode}-{report_id[:8]}.html"
                    self._send_binary(entry["html"].encode("utf-8"), "text/html; charset=utf-8", filename)
            elif path.startswith("/api/analysis-report/"):
                report_id = path[len("/api/analysis-report/"):]
                entry = report_store.get(report_id)
                if entry is None:
                    self._send_json({"error": "report not found or expired"}, 404)
                else:
                    html_bytes = entry["html"].encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(html_bytes)))
                    self.end_headers()
                    self.wfile.write(html_bytes)
            else:
                self._send_json({"error": "not found"}, 404)
    return Handler


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def viewer_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/claude-log.html"


def create_server(
    port: int,
    projects_dir: Path,
    logs_dir: Path,
    config_path: Path | None = None,
    analyzer_cmd: list[str] | tuple[str, ...] | None = None,
    adapter: AgentAdapter | None = None,
    analyzer_agent: str | None = None,
    analyzer_timeout: int | None = None,
    dataset_registry_root: Path | None = None,
) -> HTTPServer:
    handler = _make_handler(
        projects_dir,
        logs_dir,
        config_path,
        analyzer_cmd,
        adapter=adapter,
        analyzer_agent=analyzer_agent,
        analyzer_timeout=analyzer_timeout,
        dataset_registry_root=dataset_registry_root,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    server.daemon_threads = True
    return server


def open_viewer(port: int) -> None:
    webbrowser.open(viewer_url(port))


def run_server(
    port: int,
    projects_dir: Path,
    logs_dir: Path,
    config_path: Path | None = None,
    adapter: AgentAdapter | None = None,
    analyzer_agent: str | None = None,
    analyzer_timeout: int | None = None,
    dataset_registry_root: Path | None = None,
) -> None:
    server = create_server(
        port,
        projects_dir,
        logs_dir,
        config_path,
        adapter=adapter,
        analyzer_agent=analyzer_agent,
        analyzer_timeout=analyzer_timeout,
        dataset_registry_root=dataset_registry_root,
    )
    url = viewer_url(port)
    agent_name = adapter.name if adapter is not None else "claude"
    print(f"Viewer API listening on http://127.0.0.1:{port}")
    print(f"Agent         : {agent_name}")
    print(f"Projects dir  : {projects_dir.resolve()}")
    print(f"Logs dir      : {logs_dir.resolve()}")
    print(f"Open viewer   : {url}")
    print("Press Ctrl+C to stop.\n")
    open_viewer(port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


# ---------------------------------------------------------------------------
# Direct CLI (python3 viewer/server.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent session viewer API server")
    parser.add_argument("--port", type=int, default=7789)
    parser.add_argument("--projects-dir", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--logs-dir", type=Path, default=Path("./logs"))
    args = parser.parse_args()
    run_server(args.port, args.projects_dir, args.logs_dir)
