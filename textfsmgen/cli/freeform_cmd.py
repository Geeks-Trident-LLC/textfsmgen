import click

from .builder_runner import BuilderRunner

from .help_text import HELP


def register(cli):
    cli.add_command(freeform)


@click.command(
    help="Generate a TextFSM template from user input snippet.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option("--snippet", default="", help=HELP.snippet)
@click.option(
    "--snippet-file",
    default=None,
    type=click.Path(exists=True),
    help=HELP.snippet_file,
)
@click.option(
    "--sample-file",
    default=None,
    type=click.Path(exists=True),
    help=HELP.sample_file,
)
@click.option("--command", default="", help=HELP.command)
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
def freeform(ctx, **cli_options):
    runner = BuilderRunner(
        builder="freeform", usage=ctx.get_help(), cli_options=cli_options
    )

    result = runner.run()

    click.echo(result.output)
    raise SystemExit(result.exit_code)
