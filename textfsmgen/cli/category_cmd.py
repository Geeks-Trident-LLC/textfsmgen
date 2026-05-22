# textfsmgen/cli/category_cmd.py

import click

from .builder_runner import BuilderRunner

from .help_text import HELP


def register(cli):
    cli.add_command(category)


@click.command(
    help="Generate a TextFSM template from a categorized text sample.",
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
    "--count",
    default=1,
    type=int,
    show_default=True,
    help="Number of category key/value pairs to generate.",
)
@click.option(
    "--separator",
    default=":",
    show_default=True,
    help="Separator between key and value fields.",
)
@click.option(
    "--starting-from", default=None, help="Start parsing only after this marker."
)
@click.option(
    "--ending-at", default=None, help="Stop parsing when this marker is reached."
)
@click.option(
    "--replacing-rules", default=None, help="Replacing rules (string or JSON)."
)
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
def category(ctx, **cli_options):
    runner = BuilderRunner(
        builder="category", usage=ctx.get_help(), cli_options=cli_options
    )

    result = runner.run()

    click.echo(result.output)
    raise SystemExit(result.exit_code)
