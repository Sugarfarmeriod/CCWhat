from __future__ import annotations

import json


def _text_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def parse_jsonl_text(stdout: str, stderr: str = "", extra_files: dict[str, str] | None = None) -> str:
    parts: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        ev_type = ev.get("type", "")
        if ev_type == "text":
            text = _text_value(ev.get("content")) or _text_value(ev.get("text"))
            part = ev.get("part")
            if not text and isinstance(part, dict):
                text = _text_value(part.get("text")) or _text_value(part.get("content"))
            if text:
                parts.append(text)
        elif ev_type == "part":
            part = ev.get("part")
            if not isinstance(part, dict):
                continue
            part_type = part.get("type", "")
            if part_type == "text":
                text = _text_value(part.get("text")) or _text_value(part.get("content"))
                if text:
                    parts.append(text)
    return "\n".join(parts)
