"""proxy subcommand — start mitmproxy via mitmdump CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

from deep_ai_analysis.config import DEFAULT_RAW_LOG_DIR, RECORD_DOMAINS


@click.command()
@click.option(
    "--port",
    default=7788,
    show_default=True,
    type=int,
    help="Port for the proxy to listen on.",
)
@click.option(
    "--output",
    default=str(DEFAULT_RAW_LOG_DIR),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory where JSONL log files are written.",
)
def proxy(port: int, output: Path) -> None:
    """Start an HTTP/HTTPS intercepting proxy and record matching traffic to JSONL."""
    addon_path = Path(__file__).parent.parent / "addons" / "recorder.py"
    ca_cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    domains_str = ", ".join(RECORD_DOMAINS)

    output.mkdir(parents=True, exist_ok=True)

    cmd = [
        "mitmdump",
        "--listen-host", "127.0.0.1",
        "--listen-port", str(port),
        "-s", str(addon_path),
        "--set", "hardump=/dev/null",
        "--flow-detail", "0",
        "-q",
    ]

    env = os.environ.copy()
    env["DAA_OUTPUT_DIR"] = str(output.resolve())
    env["DAA_RECORD_DOMAINS"] = ",".join(RECORD_DOMAINS)

    click.echo(f"Proxy listening on http://127.0.0.1:{port}")
    click.echo(f"Recording domains : {domains_str}")
    click.echo(f"Log directory     : {output.resolve()}")
    click.echo(f"CA certificate    : {ca_cert}")
    click.echo(
        "  → Install the CA cert so HTTPS traffic is decrypted.\n"
        "  → macOS: sudo security add-trusted-cert -d -r trustRoot "
        f"-k /Library/Keychains/System.keychain {ca_cert}\n"
        f"  → Set your client's HTTP proxy to http://127.0.0.1:{port}"
    )
    click.echo("Press Ctrl+C to stop.\n")

    try:
        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo(
            "Error: mitmdump command not found.\n"
            "Install mitmproxy with:  brew install mitmproxy",
            err=True,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nProxy stopped.")
