# textfsmgen/cli/tabular_cmd.py

import click

from .builder_runner import BuilderRunner

from .help_text import HELP


def register(cli):
    cli.add_command(tabular)


@click.command(
    help="Generate a TextFSM template from a tabular text sample.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option(
    "--sample-file",
    default=None,
    type=click.Path(exists=True),
    help=HELP.sample_file,
)
@click.option(
    "--command",
    default="",
    help=HELP.command,
)
@click.option(
    "--column-divider",
    default="",
    help="Column divider string (e.g., whitespace or a specific character).",
)
@click.option(
    "--column-count",
    default=0,
    type=int,
    help="Expected number of columns in the table.",
)
@click.option(
    "--column-widths",
    default=None,
    help="Explicit column widths (comma-separated or JSON).",
)
@click.option("--headers", default=None, help="Header names (comma-separated or JSON).")
@click.option(
    "--header-rows", default=None, help="Number of header rows or explicit row indices."
)
@click.option(
    "--custom-header", default="", help="Custom header text to prepend to the template."
)
@click.option(
    "--starting-from", default=None, help="Start parsing only after this marker."
)
@click.option(
    "--ending-at", default=None, help="Stop parsing when this marker is reached."
)
@click.option(
    "--headered/--headerless",
    "has_header_row",
    is_flag=True,
    default=True,
    help="Treat the table as headered or headerless."
)
@click.option(
    "--replacing-rules", default=None, help="Replacing rules (string or JSON)."
)
@click.option(
    "--config",
    default=None,
    type=click.Path(dir_okay=False, writable=True, allow_dash=True),
    help=HELP.config,
)
@click.option("--debug", is_flag=True, default=False, help=HELP.debug)
@click.option("--dry-run", is_flag=True, default=False, help=HELP.dry_run)
@click.option("--show", default="", help=HELP.show)
@click.option("--save", default="", help=HELP.save)
@click.option(
    "--create-config",
    default=None,
    type=click.Path(dir_okay=False, writable=True, allow_dash=True),
    help=HELP.create_config,
)
@click.option(
    "--create-golden-test",
    default=None,
    type=click.Path(dir_okay=True, writable=True, allow_dash=True),
    help=HELP.create_golden_test,
)
@click.option(
    "--json",
    "json_mode",
    is_flag=True,
    default=False,
    help=HELP.json,
)
@click.pass_context
def tabular(ctx, **cli_options):
    runner = BuilderRunner(
        builder="tabular", usage=ctx.get_help(), cli_options=cli_options
    )

    result = runner.run()

    click.echo(result.output)
    raise SystemExit(result.exit_code)
