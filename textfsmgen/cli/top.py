import click
from textfsmgen import __version__

from . import category_cmd
from . import tabular_cmd
from . import freeform_cmd
from . import config_cmd


@click.group(
    invoke_without_command=True,
    help="TextFSM Generator CLI. Use 'textfsmgen tester --help' for test utilities.",
)
@click.version_option(__version__, "--version", "-v", message="textfsmgen %(version)s")
@click.pass_context
def cli(ctx):
    """Top-level command-line interface for textfsmgen."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


category_cmd.register(cli)
tabular_cmd.register(cli)
config_cmd.register(cli)
freeform_cmd.register(cli)


@cli.command(help="Show the textfsmgen version.")
def version():
    click.echo(f"textfsmgen {__version__}")
