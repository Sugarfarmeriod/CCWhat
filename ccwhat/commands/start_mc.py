"""start-mc — deprecated hidden alias, use `ccwhat -- claude` instead."""

from __future__ import annotations

import sys

import click


@click.command(
    name="start-mc",
    hidden=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def start_mc(extra_args: tuple) -> None:
    """[DEPRECATED] Use `ccwhat -- claude` instead."""
    click.echo(
        "Warning: `start-mc` is deprecated and will be removed in a future release.\n"
        "Use `ccwhat -- claude` instead:\n\n"
        "  ccwhat -- claude\n",
        err=True,
    )
    # Forward to run command for backwards compatibility
    from ccwhat.commands.run import run
    from click.testing import CliRunner

    args = ["--"] + list(extra_args) if extra_args else ["--", "claude"]
    ctx = click.get_current_context()
    ctx.invoke(run, target_args=("claude", *extra_args))
