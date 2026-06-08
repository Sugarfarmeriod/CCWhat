from __future__ import annotations

import json
import os


def parse_jsonl_text(stdout: str, stderr: str = "", extra_files: dict[str, str] | None = None) -> str:
    """Extract final assistant/agent text from Codex exec JSONL output."""
    texts: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        ev_type = ev.get("type", "")
        if ev_type == "assistant" and ev.get("content"):
            texts.append(ev["content"])
        elif ev_type == "agent" and ev.get("messages"):
            for msg in ev["messages"]:
                if msg.get("role") == "assistant" and msg.get("content"):
                    texts.append(msg["content"])
    return "\n".join(texts)


def parse_last_message_file(stdout: str, stderr: str = "", extra_files: dict[str, str] | None = None) -> str:
    tmpfile = (extra_files or {}).get("last_message_file")
    if not tmpfile or not os.path.isfile(tmpfile):
        return ""
    try:
        with open(tmpfile, encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, UnicodeDecodeError):
        return ""
