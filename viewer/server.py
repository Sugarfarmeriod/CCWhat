"""Viewer HTTP server — serves agent session log data via REST API."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ccwhat.adapters.base import AdapterNotImplementedError, AgentAdapter
from ccwhat.adapters.claude import ClaudeAdapter
from ccwhat.adapters.registry import create_adapter
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
):
    viewer_dir = Path(__file__).parent
    _adapter = adapter
    _analyzer_agent = analyzer_agent
    _analyzer_timeout = analyzer_timeout
    report_store: dict[str, dict] = {}

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
            if path not in ("/api/analyze", "/api/task-segments"):
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

            # ── /api/task-segments ─────────────────────────────────────────
            if path == "/api/task-segments":
                from ccwhat.task_segments import segment_session
                started = time.monotonic()
                result = segment_session(session)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                tasks_json = [
                    {
                        "taskId": t.task_id,
                        "title": t.title,
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
                    }
                    for t in result.tasks
                ]
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
                allowed = [report_session.project_path] if report_session.project_path else None
                report_started = time.monotonic()
                effective_agent = _analyzer_agent or self._adapter_agent() or report_session.primary_agent_type or "claude"
                if mode == "generic":
                    result = build_generic_html_report(
                        session,
                        allowed_dirs=allowed,
                        custom_prompt=custom_prompt,
                        analyzer_cmd=analyzer_cmd,
                        analyzer_agent=effective_agent,
                        analyzer_timeout=_analyzer_timeout,
                    )
                else:
                    result = build_html_session_report(
                        session,
                        allowed_dirs=allowed,
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
            if path == "/api/recording/status":
                self._send_json(get_recording_status(logs_dir, config_path))
            elif path == "/api/projects":
                try:
                    projects = self._get_sessions_data()
                    for proj in projects:
                        proj["agent"] = self._adapter_agent() or "claude"
                    self._send_json(projects)
                except AdapterNotImplementedError as exc:
                    self._send_json({"error": str(exc), "agent": self._adapter_agent() or "claude"}, 501)
            elif path.startswith("/api/session/"):
                session_id = path[len("/api/session/"):]
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
) -> HTTPServer:
    handler = _make_handler(projects_dir, logs_dir, config_path, analyzer_cmd, adapter=adapter, analyzer_agent=analyzer_agent, analyzer_timeout=analyzer_timeout)
    return HTTPServer(("127.0.0.1", port), handler)


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
) -> None:
    server = create_server(port, projects_dir, logs_dir, config_path, adapter=adapter, analyzer_agent=analyzer_agent, analyzer_timeout=analyzer_timeout)
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
