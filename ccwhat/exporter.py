"""Shared export logic — used by both the CLI command and the viewer HTTP server."""

from __future__ import annotations

import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ccwhat import __version__

_ROOT = "ccwhat-export"


def _add_file(tar: tarfile.TarFile, src: Path, arcname: str) -> None:
    tar.add(src, arcname=arcname, recursive=False)


def _add_bytes(tar: tarfile.TarFile, data: bytes, arcname: str, mode: int = 0o644) -> None:
    info = tarfile.TarInfo(name=arcname)
    info.size = len(data)
    info.mode = mode
    info.mtime = int(datetime.now().timestamp())
    tar.addfile(info, io.BytesIO(data))


def _build_manifest(sessions: list[dict[str, Any]]) -> bytes:
    manifest = {
        "exportVersion": "2.0",
        "toolName": "ccwhat",
        "toolVersion": __version__,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sessionCount": len(sessions),
        "sessions": sessions,
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False).encode()


def _build_readme(session_count: int) -> bytes:
    session_label = "1 session" if session_count == 1 else f"{session_count} sessions"
    content = f"""\
# ccwhat diagnostic package

This package contains {session_label}.

## Viewing

### Import via CLI

If you have the tar.gz archive:

```bash
ccwhat import export-xxx.tar.gz --open
```

If already extracted:

```bash
ccwhat import ./ccwhat-export --open
```

The `--open` flag starts the viewer and opens it in your browser.

## Prerequisites

Install ccwhat:

```bash
pip install ccwhat
```
"""
    return content.encode()


def _build_view_command() -> bytes:
    content = """\
#!/bin/bash
cd "$(dirname "$0")"
ccwhat import . --open
"""
    return content.encode()


def export_session(
    tar: tarfile.TarFile,
    session_id: str,
    projects_dir: Path,
    req_resp_dir: Path,
    req_resp_dates: dict[str, list[str]],
    get_session_fn: Any,
    content_options: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Add one session's files into an open TarFile using portable diagnostic format.

    get_session_fn is viewer.server.get_session, passed in to avoid circular imports.
    """
    if content_options is None:
        content_options = {"claudeLogs": True, "subagentLogs": True, "reqResp": True}

    session = get_session_fn(session_id, projects_dir)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    session_root = f"{_ROOT}/sessions/{session_id}"
    project_dir = projects_dir / session["projectDir"]
    main_log = project_dir / f"{session_id}.jsonl"
    if not main_log.exists():
        raise ValueError(f"Main Claude log not found: {main_log}")

    _add_file(tar, main_log, f"{session_root}/claude-logs/main-session.jsonl")

    subagent_count = 0
    if content_options.get("subagentLogs", True):
        subagents_dir = project_dir / session_id / "subagents"
        if subagents_dir.is_dir():
            for path in sorted(subagents_dir.iterdir()):
                if not path.is_file():
                    continue
                _add_file(tar, path, f"{session_root}/claude-logs/subagents/{path.name}")
                subagent_count += 1

    raw_count = 0
    if content_options.get("reqResp", True):
        for date in req_resp_dates.get(session_id, []):
            raw_path = req_resp_dir / session_id / f"{date}.jsonl"
            if not raw_path.exists():
                continue
            _add_file(tar, raw_path, f"{session_root}/req-resp/{raw_path.name}")
            raw_count += 1

    included = {
        "claudeLogs": True,
        "subagentLogs": content_options.get("subagentLogs", True) and subagent_count > 0,
        "reqResp": content_options.get("reqResp", True) and raw_count > 0,
    }
    counts = {"subagentFiles": subagent_count, "reqRespFiles": raw_count}

    _add_bytes(
        tar,
        json.dumps({"sessionId": session_id, "projectDir": session["projectDir"]}, indent=2).encode(),
        f"{session_root}/metadata/session.json",
    )
    _add_bytes(
        tar,
        json.dumps({"projectDir": session["projectDir"]}, indent=2).encode(),
        f"{session_root}/metadata/project.json",
    )

    return {
        "session_id": session_id,
        "project_dir": session["projectDir"],
        "subagent_count": subagent_count,
        "raw_count": raw_count,
        "manifest_entry": {
            "sessionId": session_id,
            "projectDir": session["projectDir"],
            "included": included,
            "counts": counts,
        },
    }


def build_tar_gz_bytes(
    session_ids: list[str],
    projects_dir: Path,
    req_resp_dir: Path,
    req_resp_dates: dict[str, list[str]],
    get_session_fn: Any,
    content_options: dict[str, bool] | None = None,
) -> tuple[bytes, list[dict[str, Any]]]:
    """Generate a tar.gz archive in memory and return (bytes, summaries)."""
    buf = io.BytesIO()
    summaries: list[dict[str, Any]] = []
    with tarfile.open(mode="w:gz", fileobj=buf) as tar:
        for session_id in session_ids:
            summaries.append(
                export_session(
                    tar, session_id, projects_dir, req_resp_dir,
                    req_resp_dates, get_session_fn, content_options,
                )
            )
        manifest_sessions = [summary["manifest_entry"] for summary in summaries]
        _add_bytes(tar, _build_manifest(manifest_sessions), f"{_ROOT}/manifest.json")
        _add_bytes(tar, _build_readme(len(summaries)), f"{_ROOT}/README.md")
        _add_bytes(tar, _build_view_command(), f"{_ROOT}/view.command", mode=0o755)
    return buf.getvalue(), summaries


def default_filename(session_id: str | None = None, session_count: int = 1) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    if session_count > 1:
        return f"export-{ts}-{session_count}-sessions.tar.gz"
    short_id = f"-{session_id[:8]}" if session_id else ""
    return f"export-{ts}{short_id}.tar.gz"
