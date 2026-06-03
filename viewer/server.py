"""Viewer HTTP server — serves Claude Code session log data via REST API."""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Data loading helpers
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


def _session_timestamps(jsonl_path: Path) -> tuple[str | None, str | None]:
    """Return (first_timestamp, last_timestamp) from a session JSONL file."""
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


def get_projects(projects_dir: Path) -> list[dict[str, Any]]:
    """Return list of {projectDir, sessions} for all projects."""
    result = []
    if not projects_dir.is_dir():
        return result
    for project_path in sorted(projects_dir.iterdir()):
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


def get_session(session_id: str, projects_dir: Path) -> dict[str, Any] | None:
    """Find session by ID across all project dirs. Returns None if not found."""
    if not projects_dir.is_dir():
        return None
    for project_path in projects_dir.iterdir():
        if not project_path.is_dir():
            continue
        jsonl_path = project_path / f"{session_id}.jsonl"
        if jsonl_path.exists():
            main_entries = _read_jsonl(jsonl_path)
            session_dir = project_path / session_id
            subagents = _load_subagents(session_dir)
            return {
                "sessionId": session_id,
                "projectDir": project_path.name,
                "main": main_entries,
                "subagents": subagents,
            }
    return None


def get_message_http(
    session_id: str,
    message_id: str,
    projects_dir: Path,
    logs_dir: Path,
) -> list[dict[str, Any]] | None:
    """Find HTTP records matching an assistant message ID (msg_bdrk_xxx).

    message_id is the assistant entry's message.id field.
    Matches by response_json.message.id in parsed JSONL files.

    Returns a list of matching parsed records, or None if session not found.
    Returns [] if no matching records found.
    """
    # Verify the session exists
    session_data = get_session(session_id, projects_dir)
    if session_data is None:
        return None

    # Scan all *_parsed.jsonl files in logs_dir, match by response_json.message.id
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
    """Find the source (main or subagent) of an assistant message by message.id.

    Returns:
        {"source": "main"} or {"source": "subagent", "agentId": "..."}
        None if session not found, {} if message not found in session.
    """
    session_data = get_session(session_id, projects_dir)
    if session_data is None:
        return None

    # Search main entries
    for entry in session_data.get("main", []):
        if entry.get("type") == "assistant" and entry.get("message", {}).get("id") == message_id:
            return {"source": "main"}

    # Search subagents
    for sa in session_data.get("subagents", []):
        for entry in sa.get("entries", []):
            if entry.get("type") == "assistant" and entry.get("message", {}).get("id") == message_id:
                return {"source": "subagent", "agentId": sa.get("agentId", "")}

    return {}


def get_logs(
    logs_dir: Path,
    session_filter: str | None = None,
) -> dict[str, Any]:
    """Return all parsed log records from *_parsed.jsonl files.

    Records are sorted by timestamp descending.
    Returns {"records": [...], "sessions": [...unique session ids]}.
    """
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
    """Return all session IDs and their available date files under logs_dir.

    Returns {"sessions": [{"id": "<sessionId>", "dates": ["YYYY-MM-DD", ...]}, ...]}.
    """
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
    """Return raw records from logs_dir/<session_id>/<date>.jsonl.

    SSE records have _message_id injected from the message_start event.
    Non-SSE records have _message_id set to None.
    """
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
    """Return recording config and health status for the viewer status panel.

    Never includes API keys, auth values, cookies, or sensitive header values.
    """
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
):
    viewer_dir = Path(__file__).parent

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

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")

            if path != "/api/analyze":
                self._send_json({"ok": False, "error": "not found"}, 404)
                return

            payload = self._read_json_body()
            if payload is None:
                self._send_json({"ok": False, "error": "invalid JSON body"}, 400)
                return

            session_id = str(payload.get("sessionId", "")).strip()
            if not re.fullmatch(r"[0-9a-f-]{36}", session_id):
                self._send_json({"ok": False, "error": "invalid session id"}, 400)
                return

            session = get_session(session_id, projects_dir)
            if session is None:
                self._send_json({"ok": False, "error": "session not found"}, 404)
                return

            from ccwhat.analyzer import (
                AnalysisError,
                build_analysis_prompt,
                run_mc_analysis,
            )

            prompt, truncated = build_analysis_prompt(session)
            try:
                report, elapsed_ms = run_mc_analysis(prompt, cmd=analyzer_cmd)
            except AnalysisError as exc:
                self._send_json({"ok": False, "error": exc.message, "code": exc.code}, 500)
                return

            self._send_json({
                "ok": True,
                "report": report,
                "elapsedMs": elapsed_ms,
                "truncated": truncated,
            })

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
                self._send_json(get_projects(projects_dir))

            elif path.startswith("/api/session/"):
                session_id = path[len("/api/session/"):]
                if not re.fullmatch(r"[0-9a-f-]{36}", session_id):
                    self._send_json({"error": "invalid session id"}, 400)
                    return
                data = get_session(session_id, projects_dir)
                if data is None:
                    self._send_json({"error": "session not found"}, 404)
                else:
                    self._send_json(data)

            elif path == "/api/logs":
                from urllib.parse import parse_qs
                params = parse_qs(query)
                session_filter = params.get("session", [None])[0]
                self._send_json(get_logs(logs_dir, session_filter))

            elif path.startswith("/api/message-http/"):
                # /api/message-http/<sessionId>/<messageId>
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
                # /api/message-source/<sessionId>/<messageId>
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
) -> HTTPServer:
    handler = _make_handler(projects_dir, logs_dir, config_path, analyzer_cmd)
    return HTTPServer(("127.0.0.1", port), handler)


def open_viewer(port: int) -> None:
    webbrowser.open(viewer_url(port))


def run_server(port: int, projects_dir: Path, logs_dir: Path, config_path: Path | None = None) -> None:
    server = create_server(port, projects_dir, logs_dir, config_path)
    url = viewer_url(port)
    print(f"Viewer API listening on http://127.0.0.1:{port}")
    print(f"Projects dir : {projects_dir.resolve()}")
    print(f"Logs dir     : {logs_dir.resolve()}")
    print(f"Open viewer  : {url}")
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
    parser = argparse.ArgumentParser(description="Claude Code session viewer API server")
    parser.add_argument("--port", type=int, default=7789)
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path.home() / ".claude" / "projects",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("./logs"),
    )
    args = parser.parse_args()
    run_server(args.port, args.projects_dir, args.logs_dir)
