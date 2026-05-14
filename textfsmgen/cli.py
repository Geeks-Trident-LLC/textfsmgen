"""
Top-level CLI for the textfsmgen application.

This dispatcher handles commands such as:

    textfsmgen tester run <case>
    textfsmgen tester regen <case>

All tester subcommands are forwarded to TesterCLI with correct
argument forwarding.
"""

import click
from textfsmgen import __version__
from textfsmgen.tester.cli import TesterCLI


@click.group(
    invoke_without_command=True,
    help="TextFSM Generator CLI. Use 'textfsmgen tester --help' for test utilities."
)
@click.version_option(__version__, "--version", "-V", message="textfsmgen %(version)s")
@click.pass_context
def cli(ctx):
    """Top-level command-line interface for textfsmgen."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@cli.command(
    help="Golden Master Testing utilities. All arguments after 'tester' are forwarded."
)
@click.argument("remaining", nargs=-1)
def tester(remaining):
    tester_cli = TesterCLI()
    return tester_cli.run_from_argv(list(remaining))
