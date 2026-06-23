"""Client helpers for runtime controller calls."""

from __future__ import annotations

import json
from typing import Any
import urllib.error
import urllib.request


def call_controller(port: int, token: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/{action}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-CCWhat-Run-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "error": str(exc)}
