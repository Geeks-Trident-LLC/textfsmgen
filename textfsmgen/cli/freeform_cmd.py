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
@click.option("--show", default="", help=HELP.show)
@click.option("--save", default="", help=HELP.save)
@click.option("--config", default=None, type=click.Path(exists=True), help=HELP.config)
@click.option("--debug", is_flag=True, default=False, help=HELP.debug)
@click.option("--create-config", is_flag=True, default=False, help=HELP.create_config)
@click.option(
    "--create-config-file",
    default=None,
    type=click.Path(dir_okay=False, writable=True, allow_dash=True),
    help=HELP.create_config_file,
)
@click.option("--create-golden-test", is_flag=True, help=HELP.create_golden_test)
@click.option(
    "--create-golden-test-path",
    default=None,
    type=click.Path(dir_okay=True, writable=True, allow_dash=True),
    help=HELP.create_golden_test_path,
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
