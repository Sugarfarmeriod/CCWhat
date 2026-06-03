"""run subcommand — launch an AI coding CLI through the ccwhat proxy."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
from pathlib import Path
from http.server import HTTPServer

import click

from ccwhat.config import (
    DEFAULT_RAW_LOG_DIR,
    generate_local_session_id,
    load_config,
    normalize_path,
    validate_domain,
)



def _marker_path(port: int) -> Path:
    """Return path to the ccwhat proxy marker file for this port."""
    import tempfile
    return Path(tempfile.gettempdir()) / f"ccwhat-proxy-{port}.pid"


def _proxy_port_in_use(port: int) -> bool:
    """Return True if something is listening on localhost:port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _proxy_is_running(port: int) -> bool:
    """Return True if a ccwhat-managed proxy is listening on this port.

    Raises SystemExit if the port is occupied by a non-ccwhat process.
    """
    if not _proxy_port_in_use(port):
        return False
    marker = _marker_path(port)
    if marker.exists():
        try:
            pid = int(marker.read_text().strip())
        except (ValueError, OSError):
            pid = None
        # Verify the process is still alive
        if pid is not None:
            try:
                os.kill(pid, 0)  # signal 0 = existence check
                return True
            except (ProcessLookupError, PermissionError):
                pass
        marker.unlink(missing_ok=True)
    # Port is occupied but no ccwhat marker — refuse to proceed
    click.echo(
        f"Error: port {port} is already in use by another process "
        "(not a ccwhat proxy).\n"
        f"Use a different port: ccwhat --port <other-port> -- <cli>",
        err=True,
    )
    sys.exit(1)


def _start_managed_proxy(
    port: int,
    output: Path,
    effective_domains: list[str],
    effective_paths: list[str],
    max_body_bytes: int,
    redact_headers: list[str],
    redact_patterns: list[str],
    local_session_id: str,
) -> subprocess.Popen | None:
    """Start mitmdump as a background process. Returns the Popen handle or None on failure."""
    addon_path = Path(__file__).parent.parent / "addons" / "recorder.py"
    output.mkdir(parents=True, exist_ok=True)

    cmd = [
        "mitmdump",
        "--listen-host", "127.0.0.1",
        "--listen-port", str(port),
        "-s", str(addon_path),
        "--set", f"hardump={os.devnull}",
        "--flow-detail", "0",
        "-q",
    ]

    env = os.environ.copy()
    env["CCWHAT_OUTPUT_DIR"] = str(output.resolve())
    env["CCWHAT_RECORD_DOMAINS"] = ",".join(effective_domains)
    env["CCWHAT_RECORD_PATHS"] = ",".join(effective_paths)
    env["CCWHAT_MAX_BODY_BYTES"] = str(max_body_bytes)
    env["CCWHAT_REDACT_HEADERS"] = ",".join(redact_headers)
    env["CCWHAT_REDACT_PATTERNS"] = ",".join(redact_patterns)
    env["CCWHAT_LOCAL_SESSION_ID"] = local_session_id

    try:
        proc = subprocess.Popen(cmd, env=env)
    except FileNotFoundError:
        click.echo(
            "Error: mitmdump command not found.\n"
            "Install mitmproxy with:  brew install mitmproxy",
            err=True,
        )
        return None

    # Brief wait for proxy to bind (up to 2 s)
    import time
    bound = False
    for _ in range(20):
        # Check process is still alive
        if proc.poll() is not None:
            break
        if _proxy_port_in_use(port):
            bound = True
            break
        time.sleep(0.1)

    if not bound or proc.poll() is not None:
        # Proxy failed to start — terminate any still-running process, clean up
        returncode = proc.poll()
        if returncode is None:
            # Process is alive but never bound — kill it to avoid orphan
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            returncode = proc.poll()
        click.echo(
            f"Error: managed proxy failed to bind on port {port}"
            + (f" (exit code {returncode})" if returncode is not None else "")
            + ".\nCheck that mitmproxy is installed and the port is free.",
            err=True,
        )
        _marker_path(port).unlink(missing_ok=True)
        return None

    # Write marker only after successful bind
    try:
        _marker_path(port).write_text(str(proc.pid))
    except OSError:
        pass

    return proc


def _start_managed_web(
    port: int,
    req_resp_dir: Path,
    config_path: Path | None,
    analyzer_cmd: tuple[str, ...],
) -> HTTPServer | None:
    from viewer.server import create_server, open_viewer, viewer_url

    url = viewer_url(port)
    if _proxy_port_in_use(port):
        click.echo(f"Viewer: {url}")
        open_viewer(port)
        return None

    projects_dir = Path.home() / ".claude" / "projects"
    try:
        server = create_server(port, projects_dir, req_resp_dir, config_path, analyzer_cmd)
    except OSError:
        click.echo(f"Viewer may already be running: {url}")
        open_viewer(port)
        return None

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    click.echo(f"Viewer: {url}")
    open_viewer(port)
    return server


def _stop_managed_web(server: HTTPServer | None) -> None:
    if server is None:
        return
    server.shutdown()
    server.server_close()


@click.command(
    "run",
    hidden=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@click.option("--port", default=7788, show_default=True, type=int, help="Proxy port.")
@click.option("--web/--no-web", default=True, show_default=True, help="Start and open the viewer.")
@click.option("--web-port", default=7789, show_default=True, type=int, help="Viewer port.")
@click.option(
    "--output",
    default=str(DEFAULT_RAW_LOG_DIR),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory where JSONL log files are written.",
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to config.toml.",
)
@click.option("--no-setup", is_flag=True, help="Skip onboarding even if no config exists.")
@click.argument("target_args", nargs=-1, type=click.UNPROCESSED)
def run(
    port: int,
    web: bool,
    web_port: int,
    output: Path,
    config_path: Path | None,
    no_setup: bool,
    target_args: tuple[str, ...],
) -> None:
    """Launch a command through the ccwhat proxy with env vars injected.

    Example:

      ccwhat -- claude
      ccwhat -- my-ai-cli --model sonnet
    """
    if not target_args:
        click.echo(
            "Error: no target command provided.\n\n"
            "Usage: ccwhat -- <command> [args...]\n\n"
            "Examples:\n"
            "  ccwhat -- claude\n"
            "  ccwhat -- mc --code\n"
            "  ccwhat -- my-ai-cli --model sonnet --resume",
            err=True,
        )
        sys.exit(1)

    cfg = load_config(config_path)

    if not no_setup and (cfg is None or not cfg.is_valid_for_recording()):
        is_interactive = sys.stdin.isatty()
        if is_interactive:
            click.echo(
                "No recording configuration found.\n"
                "Starting first-run setup wizard...\n"
            )
            from ccwhat.commands.setup import _run_setup_wizard
            cfg = _run_setup_wizard(config_path)
        else:
            click.echo(
                "Error: no recording domains configured. Set up recording with:\n"
                "  ccwhat setup --preset claude --yes\n"
                "  ccwhat discover\n"
                "Or pass --no-setup to launch without payload recording.",
                err=True,
            )
            sys.exit(1)

    if no_setup or cfg is None or not cfg.is_valid_for_recording():
        effective_domains: list[str] = []
        effective_paths: list[str] = []
        from ccwhat.config import DEFAULT_MAX_BODY_BYTES, DEFAULT_REDACT_HEADERS, DEFAULT_REDACT_PATTERNS
        max_body_bytes = DEFAULT_MAX_BODY_BYTES
        redact_headers = list(DEFAULT_REDACT_HEADERS)
        redact_patterns = list(DEFAULT_REDACT_PATTERNS)
        if no_setup:
            click.echo("Note: payload recording disabled (--no-setup). Traffic is proxied for discovery only.")
    else:
        effective_domains = cfg.effective_domains()
        effective_paths = cfg.effective_paths()
        max_body_bytes = cfg.max_body_bytes
        redact_headers = cfg.redact_headers
        redact_patterns = cfg.redact_header_patterns

    local_session_id = generate_local_session_id()
    proxy_proc: subprocess.Popen | None = None
    web_server: HTTPServer | None = None

    if _proxy_is_running(port):
        click.echo(f"Reusing existing ccwhat proxy on port {port}.")
    else:
        if effective_domains:
            click.echo(f"Starting proxy on port {port}...")
            click.echo(f"Recording domains : {', '.join(effective_domains)}")
            if effective_paths:
                click.echo(f"Path filters      : {', '.join(effective_paths)}")
            click.echo(f"Log directory     : {output.resolve()}")
            click.echo("Viewer hint       : ccwhat web\n")

        proxy_proc = _start_managed_proxy(
            port, output, effective_domains, effective_paths,
            max_body_bytes, redact_headers, redact_patterns, local_session_id,
        )
        if proxy_proc is None:
            sys.exit(1)

    if web:
        web_server = _start_managed_web(web_port, output, config_path, target_args)

    # Build child environment
    ca_cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    child_env = os.environ.copy()
    child_env["HTTPS_PROXY"] = f"http://127.0.0.1:{port}"
    child_env["HTTP_PROXY"] = f"http://127.0.0.1:{port}"
    child_env["NODE_EXTRA_CA_CERTS"] = str(ca_cert)
    # NO_PROXY is preserved unless already overridden

    target_proc: subprocess.Popen | None = None
    exit_code = 1

    try:
        target_proc = subprocess.Popen(list(target_args), env=child_env)
        exit_code = target_proc.wait()
    except FileNotFoundError:
        click.echo(f"Error: command not found: {target_args[0]}", err=True)
        exit_code = 127
    except KeyboardInterrupt:
        if target_proc:
            try:
                target_proc.send_signal(signal.SIGINT)
                exit_code = target_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                target_proc.kill()
                exit_code = target_proc.wait()
    finally:
        if proxy_proc is not None:
            proxy_proc.terminate()
            try:
                proxy_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_proc.kill()
            _marker_path(port).unlink(missing_ok=True)
        _stop_managed_web(web_server)

    sys.exit(exit_code)
