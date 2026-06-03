"""web-server subcommand — start the Claude Code session viewer HTTP server."""

from __future__ import annotations

from pathlib import Path

import click

from deep_ai_analysis.config import DEFAULT_RAW_LOG_DIR


@click.command("web-server")
@click.option(
    "--port",
    default=7789,
    show_default=True,
    type=int,
    help="Port for the viewer API server.",
)
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
def web_server(port: int, projects_dir: Path, req_resp_dir: Path) -> None:
    """Start the Claude Code session viewer API server."""
    import sys
    from pathlib import Path as _Path

    project_root = _Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from viewer.server import run_server
    run_server(port, projects_dir, req_resp_dir)
