"""export subcommand — bundle Claude Code logs and raw request/response logs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import click

from deep_ai_analysis.config import DEFAULT_RAW_LOG_DIR
from deep_ai_analysis.exporter import build_tar_gz_bytes, default_filename

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from viewer.server import get_projects, get_req_resp_sessions, get_session

SESSION_ID_RE = re.compile(r"[0-9a-f-]{36}")


def _print_sessions(projects_dir: Path) -> None:
    projects = get_projects(projects_dir)
    if not projects:
        click.echo(f"No Claude Code sessions found in {projects_dir}")
        return

    total = 0
    for project in projects:
        click.echo(project["projectDir"])
        for session in project["sessions"]:
            first = session.get("firstTimestamp") or "-"
            last = session.get("lastTimestamp") or "-"
            click.echo(f"  {session['id']}  {first} ~ {last}")
            total += 1

    click.echo(f"\nTotal sessions: {total}")


def _req_resp_dates_by_session(req_resp_dir: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for session in get_req_resp_sessions(req_resp_dir)["sessions"]:
        result[session["id"]] = session["dates"]
    return result


def _validate_session_ids(session_ids: tuple[str, ...]) -> list[str]:
    unique_ids = list(dict.fromkeys(session_ids))
    invalid_ids = [session_id for session_id in unique_ids if not SESSION_ID_RE.fullmatch(session_id)]
    if invalid_ids:
        raise click.ClickException(f"Invalid session ID(s): {', '.join(invalid_ids)}")
    return unique_ids


@click.command("export")
@click.argument("session_ids", nargs=-1)
@click.option(
    "--projects-dir",
    default=str(Path.home() / ".claude" / "projects"),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Path to the Claude Code projects directory.",
)
@click.option(
    "--req-resp-dir",
    default=str(DEFAULT_RAW_LOG_DIR),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory containing raw HTTP request/response JSONL files.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output archive path. Defaults to ~/Downloads/deep-ai-analysis-exports/export-<timestamp>-<id>.tar.gz.",
)
@click.option(
    "--list",
    "list_only",
    is_flag=True,
    help="List available Claude Code sessions and exit.",
)
def export(
    session_ids: tuple[str, ...],
    projects_dir: Path,
    req_resp_dir: Path,
    output: Path | None,
    list_only: bool,
) -> None:
    """Export Claude Code logs and raw request/response logs into a tar.gz archive."""
    if list_only:
        _print_sessions(projects_dir)
        return

    if not session_ids:
        raise click.ClickException("No session IDs provided. Use --list to discover available sessions.")

    resolved_session_ids = _validate_session_ids(session_ids)
    first_id = resolved_session_ids[0] if len(resolved_session_ids) == 1 else None
    if output is None:
        default_dir = Path.home() / "Downloads" / "deep-ai-analysis-exports"
        default_dir.mkdir(parents=True, exist_ok=True)
        output = default_dir / default_filename(first_id, len(resolved_session_ids))
    output.parent.mkdir(parents=True, exist_ok=True)

    req_resp_dates = _req_resp_dates_by_session(req_resp_dir)

    try:
        data, summaries = build_tar_gz_bytes(
            resolved_session_ids, projects_dir, req_resp_dir, req_resp_dates, get_session
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    output.write_bytes(data)

    click.echo(f"Exported package with {len(summaries)} session(s) to {output}")
    for summary in summaries:
        raw_note = " (no raw req/resp found)" if summary["raw_count"] == 0 else ""
        click.echo(
            f"- {summary['session_id']} [{summary['project_dir']}]: "
            f"{summary['subagent_count']} subagent files, {summary['raw_count']} raw log files{raw_note}"
        )
    click.echo("\n发给别人后，对方把压缩包放到 Downloads，然后运行这一条命令导入包内所有 session：")
    click.echo(f"  deep-ai-analysis import {output} --open")
