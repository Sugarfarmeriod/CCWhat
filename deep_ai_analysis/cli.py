"""Main CLI entry point for deep-ai-analysis."""

import click

from deep_ai_analysis import __version__
from deep_ai_analysis.commands.clear_req_resp import clear_req_resp
from deep_ai_analysis.commands.export import export
from deep_ai_analysis.commands.import_ import import_
from deep_ai_analysis.commands.proxy import proxy
from deep_ai_analysis.commands.start_mc import start_mc
from deep_ai_analysis.commands.web_server import web_server


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="deep-ai-analysis")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """deep-ai-analysis — CLI toolkit for intercepting and analyzing AI service traffic."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(proxy)
cli.add_command(start_mc)
cli.add_command(clear_req_resp)
cli.add_command(export)
cli.add_command(import_)
cli.add_command(web_server)
