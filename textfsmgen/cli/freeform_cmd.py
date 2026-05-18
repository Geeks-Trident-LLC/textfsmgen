import click
from textfsmgen.core.builder import FreeFormBuilder

from textfsmgen.cli.shared_builder_cli import (
    merge,
    validate_config,
    run_builder_workflow,
)


def register(cli):
    cli.add_command(freeform)


@click.command(
    help="Generate a TextFSM template from user input snippet.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.option("--snippet", default="", help="Inline snippet text.")
@click.option(
    "--snippet-file",
    default=None,
    type=click.Path(exists=True),
    help="Path to snippet file.",
)
@click.option(
    "--sample-file",
    default=None,
    type=click.Path(exists=True),
    help="Sample filename containing raw text sample.",
)
@click.option(
    "--command",
    "cmd",
    default="",
    help="Shell command to generate a real-world sample.",
)
@click.option(
    "--show",
    default="",
    help="Show output: snippet, template, result, tabular, or json(...).",
)
@click.option(
    "--save", default="", help="Save output to file(s). Format: type-filename."
)
@click.option(
    "--config",
    default=None,
    type=click.Path(exists=True),
    help="Optional JSON config file.",
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print resolved parameters and sample metadata.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Simulate save actions without writing files.",
)
@click.pass_context
def freeform(
    ctx, snippet, snippet_file, sample_file, cmd, save, show, config, debug, dry_run
):
    """
    Build a template from free-form snippet text.
    """

    # Show help if nothing provided
    if not snippet and not snippet_file and config is None:
        click.echo(ctx.get_help())
        raise SystemExit(0)

    # Load config
    config_data = {}
    if config:
        required_top = [
            "builder", "params", "snippet", "snippet_file",
            "sample_file", "command", "show", "save"
        ]
        required_params = []
        status = validate_config(config, required_top, required_params)
        if not status:
            raise SystemExit(1)
        config_data = status.raw or {}

    params = {}

    # Merge CLI + config
    snippet_ = merge(snippet, config_data, "snippet", "")
    snippet_file_ = merge(snippet_file, config_data, "snippet_file", "")
    sample_file_ = merge(sample_file, config_data, "sample_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    params = {}

    # Delegate to shared workflow
    exit_code = run_builder_workflow(
        FreeFormBuilder,
        snippet=snippet_,
        snippet_file=snippet_file_,
        sample_file=sample_file_,
        cmd=cmd_,
        params=params,
        save=save_,
        show=show_,
        config=config_data,
        debug=debug,
        dry_run=dry_run,
    )
    raise SystemExit(exit_code)
