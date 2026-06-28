"""Codex hook entry point for CCWhat slash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from ccwhat.runtime.http.client import call_controller


_SENTINEL_RE = re.compile(r"CCWHAT_COMMAND=(?P<command>[a-z]+)(?:\s+CCWHAT_ARGS=(?P<args>.*))?", re.S)
_SLASH_RE = re.compile(r"/(?:prompts:)?ccwhat[-:/](?P<command>start|finish)(?:\s+(?P<args>.*))?", re.S)
_TEXT_RE = re.compile(
    r"^\s*ccwhat\s+(?P<command>start|finish)(?:\s+(?P<args>.*))?\s*$",
    re.I | re.S,
)


def main() -> int:
    event = _read_event()
    text = "\n".join(_strings(event))
    parsed = _parse_command(text)
    if parsed is None:
        return 0
    command, raw_args = parsed
    if command in {"start", "finish"}:
        raw_args = ""

    port = os.environ.get("CCWHAT_RUNTIME_CONTROL_PORT")
    token = os.environ.get("CCWHAT_RUNTIME_TOKEN", "")
    if not port:
        _emit_block("CCWhat runtime controller is not available for this Codex session.")
        return 0

    payload: dict[str, Any] = {
        "raw_args": raw_args,
        "agent": "codex",
        "integration": "codex_user_prompt_submit",
        "model_visible": False,
        "agent_log_visible": False,
        "confidence": "high",
    }
    result = call_controller(int(port), token, command, payload)
    if result.get("ok"):
        task = result.get("data") or {}
        task_id = task.get("task_id") or task.get("active_task_id") or ""
        _emit_block(f"CCWhat {command} recorded locally" + (f" ({task_id})." if task_id else "."))
        return 0
    _emit_block(f"CCWhat {command} failed: {result.get('error') or 'unknown error'}")
    return 0


def _read_event() -> Any:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"prompt": raw}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_strings(item))
        return out
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_strings(item))
        return out
    return []


def _parse_command(text: str) -> tuple[str, str] | None:
    match = _SENTINEL_RE.search(text)
    if match:
        return match.group("command"), _clean_args(match.group("args") or "")
    match = _SLASH_RE.search(text)
    if match:
        return match.group("command"), _clean_args(match.group("args") or "")
    match = _TEXT_RE.search(text)
    if match:
        command = match.group("command").lower()
        return command, _clean_args(match.group("args") or "")
    return None


def _clean_args(raw: str) -> str:
    args = raw.strip().strip('"')
    return "" if args == "$ARGUMENTS" else args


def _emit_block(message: str) -> None:
    payload = {
        "decision": "block",
        "reason": message,
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
