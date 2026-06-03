"""start-mc subcommand — launch mc --code with proxy environment variables injected."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click


@click.command(
    name="start-mc",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@click.option(
    "--port",
    default=7788,
    show_default=True,
    type=int,
    help="Proxy port to point HTTPS_PROXY at.",
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def start_mc(port: int, extra_args: tuple) -> None:
    """Launch mc --code with HTTPS_PROXY and NODE_EXTRA_CA_CERTS set."""
    ca_cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"

    if not ca_cert.exists():
        click.echo(
            f"Warning: CA certificate not found at {ca_cert}\n"
            "  Run `deep-ai-analysis proxy` first to generate it, "
            "otherwise mc may fail with TLS errors.",
            err=True,
        )

    env = os.environ.copy()
    env["HTTPS_PROXY"] = f"http://127.0.0.1:{port}"
    env["NODE_EXTRA_CA_CERTS"] = str(ca_cert)

    try:
        result = subprocess.run(["mc", "--code", *extra_args], env=env)
    except FileNotFoundError:
        click.echo(
            "Error: mc command not found. Please install mc first.",
            err=True,
        )
        sys.exit(1)

    sys.exit(result.returncode)
