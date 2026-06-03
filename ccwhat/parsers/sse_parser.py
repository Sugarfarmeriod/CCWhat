"""Parse a raw proxy JSONL record into a cleaned, structured record."""

from __future__ import annotations

import json
from typing import Any


def parse_sse_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw SSE proxy record into a cleaned structured record.

    Args:
        raw: A single record from the proxy JSONL log (must have is_sse=True).

    Returns:
        Cleaned record with keys: timestamp, domain, method, url,
        claude_session_id, request_json, response_json.

    Raises:
        ValueError: If request.body is not valid JSON.
    """
    # --- request_json ---
    request_json = json.loads(raw["request"]["body"])

    # --- claude_session_id ---
    headers = raw["request"].get("headers", {})
    claude_session_id = headers.get("X-Claude-Code-Session-Id", None)

    # --- response_json: reconstruct from sse_events ---
    # blocks: index -> {type, name, id, text, input_json}
    blocks: dict[int, dict[str, Any]] = {}
    stop_reason: str | None = None
    usage: dict[str, Any] | None = None

    message_id: str | None = None
    model: str | None = None

    for event_text in raw.get("sse_events", []):
        for line in event_text.split("\n"):
            if not line.startswith("data:"):
                continue
            data_str = line[len("data:"):].strip()
            if data_str == "[DONE]":
                continue
            try:
                d = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            event_type = d.get("type")

            if event_type == "message_start":
                msg = d.get("message", {})
                message_id = msg.get("id")
                model = msg.get("model")
                if msg.get("usage"):
                    usage = {**(usage or {}), **msg["usage"]}

            elif event_type == "content_block_start":
                idx = d.get("index", 0)
                cb = d.get("content_block", {})
                blocks[idx] = {
                    "type": cb.get("type", "unknown"),
                    "name": cb.get("name"),
                    "id": cb.get("id"),
                    "text": "",
                    "input_json": "",
                }

            elif event_type == "content_block_delta":
                idx = d.get("index", 0)
                delta = d.get("delta", {})
                if idx not in blocks:
                    blocks[idx] = {"type": "unknown", "name": None, "id": None, "text": "", "input_json": ""}
                if delta.get("type") == "text_delta" and delta.get("text"):
                    blocks[idx]["text"] += delta["text"]
                elif delta.get("type") == "input_json_delta" and delta.get("partial_json"):
                    blocks[idx]["input_json"] += delta["partial_json"]

            elif event_type == "message_delta":
                delta = d.get("delta", {})
                if delta.get("stop_reason"):
                    stop_reason = delta["stop_reason"]
                if d.get("usage"):
                    usage = {**(usage or {}), **d["usage"]}

    # Build contents array in index order
    contents = []
    for _, b in sorted(blocks.items()):
        item: dict[str, Any] = {"type": b["type"]}
        if b["name"]:
            item["name"] = b["name"]
        if b["id"]:
            item["id"] = b["id"]
        if b["type"] == "text":
            item["text"] = b["text"]
        elif b["type"] == "tool_use":
            item["text"] = b["text"]
            try:
                item["input"] = json.loads(b["input_json"])
            except json.JSONDecodeError:
                item["input"] = b["input_json"]

    message: dict[str, Any] = {}
    if message_id:
        message["id"] = message_id
    if model:
        message["model"] = model
    if stop_reason:
        message["stop_reason"] = stop_reason
    if usage:
        message["usage"] = usage
    message["content"] = contents

    response_json = {"message": message}

    return {
        "timestamp": raw["timestamp"],
        "domain": raw["domain"],
        "method": raw["method"],
        "url": raw["url"],
        "claude_session_id": claude_session_id,
        "claude_message_id": message_id,
        "request_json": request_json,
        "response_json": response_json,
    }
