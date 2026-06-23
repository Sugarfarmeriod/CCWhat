"""Localhost HTTP controller for runtime task commands."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from typing import Any
from urllib.parse import urlparse

from ccwhat.runtime.registry import RunRegistry
from ccwhat.runtime.staging import ControlEvidence, RuntimeTaskError, TaskStaging


class RuntimeController:
    def __init__(self, registry: RunRegistry, run_id: str, port: int) -> None:
        self.registry = registry
        self.run_id = run_id
        self.port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        handler = self._make_handler()
        self._server = ThreadingHTTPServer(("127.0.0.1", self.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        registry = self.registry
        run_id = self.run_id
        staging = TaskStaging(registry)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                return

            def do_GET(self) -> None:
                if urlparse(self.path).path != "/status":
                    self._send({"ok": False, "error": "not found"}, status=404)
                    return
                self._handle("status", {})

            def do_POST(self) -> None:
                action = urlparse(self.path).path.strip("/")
                if action not in {"start", "finish", "status", "abort", "note"}:
                    self._send({"ok": False, "error": "not found"}, status=404)
                    return
                self._handle(action, self._read_body())

            def _handle(self, action: str, body: dict[str, Any]) -> None:
                try:
                    run = registry.load(run_id)
                    token = str(run.control.get("token") or "")
                    supplied = self.headers.get("X-CCWhat-Run-Token") or str(body.get("token") or "")
                    if token and supplied != token:
                        self._send({"ok": False, "error": "unauthorized"}, status=403)
                        return
                    evidence = ControlEvidence(
                        command=action,
                        raw_args=str(body.get("raw_args") or body.get("title") or ""),
                        agent=str(body.get("agent") or run.agent),
                        integration=str(body.get("integration") or "local_http"),
                        model_visible=bool(body.get("model_visible", False)),
                        agent_log_visible=bool(body.get("agent_log_visible", False)),
                        confidence=str(body.get("confidence") or "high"),
                    )
                    if action == "start":
                        data = staging.start_task(run, str(body.get("title") or ""), evidence)
                    elif action == "finish":
                        data = staging.finish_task(run, evidence)
                    elif action == "abort":
                        data = staging.abort_task(run, evidence)
                    elif action == "note":
                        data = staging.note(run, evidence)
                    else:
                        data = staging.status(run, evidence)
                    self._send({"ok": True, "data": data})
                except RuntimeTaskError as exc:
                    self._send({"ok": False, "error": str(exc)}, status=409)
                except Exception as exc:  # pragma: no cover - defensive for hook UX
                    self._send({"ok": False, "error": str(exc)}, status=500)

            def _read_body(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length") or "0")
                if length <= 0:
                    return {}
                try:
                    raw = self.rfile.read(length).decode("utf-8")
                    data = json.loads(raw)
                    return data if isinstance(data, dict) else {}
                except json.JSONDecodeError:
                    return {}

            def _send(self, payload: dict[str, Any], status: int = 200) -> None:
                raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        return Handler
