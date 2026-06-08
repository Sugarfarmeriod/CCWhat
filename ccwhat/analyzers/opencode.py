from __future__ import annotations

import json


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
            parts.append(ev.get("content", ""))
        elif ev_type == "part":
            part_type = ev.get("part", {}).get("type", "")
            if part_type == "text":
                parts.append(ev.get("part", {}).get("content", ""))
    return "\n".join(parts)
