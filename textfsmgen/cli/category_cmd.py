# textfsmgen/cli/category_cmd.py

import click
from textfsmgen import CategoryTemplateBuilder
from textfsmgen.cli.shared_builder_cli import (
    merge,
    validate_config,
    run_builder_workflow,
)


def register(cli):
    cli.add_command(category)


@click.command(
    help="Category builder for snippet/template/result generation.",
    context_settings=dict(help_option_names=["-h", "--help"]),
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
    help="Print resolved parameters and input metadata.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Simulate save actions without writing files.",
)
@click.pass_context
def category(
    ctx,
    sample_file,
    cmd,
    count,
    separator,
    starting_from,
    ending_at,
    replacing_rules,
    show,
    save,
    config,
    debug,
    dry_run,
):
    # Show help if nothing provided
    if not sample_file and not cmd and config is None:
        click.echo(ctx.get_help())
        raise SystemExit(0)

    # Load config
    config_data = {}
    if config:
        required = [
            "count",
            "separator",
            "starting_from",
            "ending_at",
            "replacing_rules",
        ]
        status = validate_config(config, required)
        if not status:
            raise SystemExit(1)
        config_data = status.raw or {}

    # Merge CLI + config
    sample_file_ = merge(sample_file, config_data, "sample_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    params = {
        "count": merge(count, config_data, "count", 1),
        "separator": merge(separator, config_data, "separator", ":"),
        "starting_from": merge(starting_from, config_data, "starting_from", None),
        "ending_at": merge(ending_at, config_data, "ending_at", None),
        "replacing_rules": merge(replacing_rules, config_data, "replacing_rules", None),
    }

    # Delegate to shared workflow
    exit_code = run_builder_workflow(
        CategoryTemplateBuilder,
        sample_file_,
        cmd_,
        params,
        save_,
        show_,
        config_data,
        debug,
        dry_run,
    )
    raise SystemExit(exit_code)
