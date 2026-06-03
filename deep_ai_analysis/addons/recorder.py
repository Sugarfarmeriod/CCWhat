"""mitmproxy addon that records HTTP/HTTPS traffic to JSONL files."""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mitmproxy import http

# Output directory is passed via environment variable when launched via mitmdump CLI
_DEFAULT_OUTPUT_DIR = Path.home() / ".deep-ai-analysis" / "raw-req-resp"
_OUTPUT_DIR = Path(os.environ.get("DAA_OUTPUT_DIR", str(_DEFAULT_OUTPUT_DIR)))
_DEFAULT_RECORD_DOMAINS = ["mcli.sankuai.com"]

# Headers that must never be written to log files (lowercase for case-insensitive matching)
SENSITIVE_HEADERS: frozenset[str] = frozenset({"authorization"})


def _record_domains_from_env() -> list[str]:
    raw_domains = os.environ.get("DAA_RECORD_DOMAINS")
    if raw_domains is None:
        return list(_DEFAULT_RECORD_DOMAINS)
    return [domain.strip() for domain in raw_domains.split(",") if domain.strip()]


class RecorderAddon:
    """Records matching HTTP flows to a daily JSONL file.

    Each request is written as a single JSON line to ``<output_dir>/<sessionId>/YYYY-MM-DD.jsonl``.
    SSE (text/event-stream) responses are buffered in memory and written as one
    record when the flow completes.
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self._output_dir = output_dir if output_dir is not None else _OUTPUT_DIR
        self._domains: list[str] = _record_domains_from_env()
        # Per-flow SSE state: flow_id -> {"events": [...], "buffer": ""}
        self._sse_buffers: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _should_record(self, flow: http.HTTPFlow) -> bool:
        return flow.request.pretty_host in self._domains

    def _jsonl_path(self, session_id: str) -> Path:
        today = date.today().isoformat()  # YYYY-MM-DD
        path = self._output_dir / session_id / f"{today}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _append_record(self, record: dict[str, Any], session_id: str) -> None:
        path = self._jsonl_path(session_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _headers_to_dict(self, headers: Any) -> dict[str, str]:
        return dict(headers)

    def _request_headers_to_dict(self, headers: Any) -> dict[str, str]:
        """Convert request headers to dict, excluding sensitive headers."""
        return {k: v for k, v in headers.items() if k.lower() not in SENSITIVE_HEADERS}

    # ------------------------------------------------------------------
    # mitmproxy hooks
    # ------------------------------------------------------------------

    def responseheaders(self, flow: http.HTTPFlow) -> None:
        """Detect SSE responses and enable streaming mode."""
        if not self._should_record(flow):
            return
        if flow.response is None:
            return
        content_type = flow.response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # Enable streaming: response body will arrive in chunks
            flow.response.stream = self._make_sse_stream_handler(flow)
            self._sse_buffers[flow.id] = {"events": [], "buffer": ""}

    def _make_sse_stream_handler(self, flow: http.HTTPFlow):
        """Return a streaming callback that buffers SSE chunks for this flow."""

        def handler(chunk: bytes) -> bytes:
            state = self._sse_buffers.get(flow.id)
            if state is None:
                return chunk
            text = state["buffer"] + chunk.decode("utf-8", errors="replace")
            # Split on double-newline (SSE event boundary)
            parts = text.split("\n\n")
            # All parts except the last are complete events
            for event in parts[:-1]:
                event = event.strip()
                if event:
                    state["events"].append(event)
            # The last part may be incomplete — keep it in the buffer
            state["buffer"] = parts[-1]
            return chunk  # pass through unchanged

        return handler

    def response(self, flow: http.HTTPFlow) -> None:
        """Write the completed flow to JSONL."""
        if not self._should_record(flow):
            return
        if flow.response is None:
            return

        timestamp = datetime.now(tz=timezone.utc).isoformat()

        # Extract session ID from request headers for scoped log path
        session_id = flow.request.headers.get("X-Claude-Code-Session-Id", "unknown")

        # Request fields
        try:
            req_body = flow.request.get_text(strict=False) or ""
        except Exception:
            req_body = flow.request.content.decode("utf-8", errors="replace")

        request_data = {
            "headers": self._request_headers_to_dict(flow.request.headers),
            "body": req_body,
        }

        # SSE vs normal response
        sse_state = self._sse_buffers.pop(flow.id, None)
        is_sse = sse_state is not None

        if is_sse:
            # Flush any remaining buffered text as a final (possibly incomplete) event
            remaining = sse_state["buffer"].strip()
            if remaining:
                sse_state["events"].append(remaining)
            sse_events: list[str] = sse_state["events"]
            resp_body = "\n\n".join(sse_events)
        else:
            try:
                resp_body = flow.response.get_text(strict=False) or ""
            except Exception:
                resp_body = flow.response.content.decode("utf-8", errors="replace")
            sse_events = []

        response_data = {
            "status": flow.response.status_code,
            "headers": self._headers_to_dict(flow.response.headers),
            "body": resp_body,
        }

        record: dict[str, Any] = {
            "timestamp": timestamp,
            "domain": flow.request.pretty_host,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "request": request_data,
            "response": response_data,
            "is_sse": is_sse,
        }
        if is_sse:
            record["sse_events"] = sse_events

        try:
            self._append_record(record, session_id)
        except OSError as exc:
            print(f"[deep-ai-analysis] Failed to write log: {exc}", file=sys.stderr)


# Module-level addon instance required by `mitmdump -s <this_file>`
addons = [RecorderAddon()]
