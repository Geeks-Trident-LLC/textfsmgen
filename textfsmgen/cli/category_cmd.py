# textfsmgen/cli/category_cmd.py

import click

from textfsmgen.libs.generic import StatusString, emit_status
from textfsmgen import CategoryTemplateBuilder

from textfsmgen.cli.shared_builder_cli import (
    merge, validate_config, run_builder_workflow
)

# ------------------------------------------------------------
# CLI Registration
# ------------------------------------------------------------
def register(cli):
    cli.add_command(category)


# ------------------------------------------------------------
# Main CLI Command
# ------------------------------------------------------------
@click.command(
    help="Category builder for snippet/template/result generation.",
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option(
    "--input-file",
    default=None,
    type=click.Path(exists=True),
    help="Input filename (default: empty)."
)
@click.option(
    "--command",
    "cmd",
    default="",
    help="Shell command to generate real-world sample (default: empty)."
)
@click.option(
    "--count",
    default=1,
    type=int,
    show_default=True,
    help="Number of category pairs to generate."
)
@click.option(
    "--separator",
    default=":",
    show_default=True,
    help="Separator between key/value pairs."
)
@click.option(
    "--starting-from",
    default=None,
    help="Starting-from marker (default: empty)."
)
@click.option(
    "--ending-at",
    default=None,
    help="Ending-at marker (default: empty)."
)
@click.option(
    "--replacing-rules",
    default=None,
    help="Replacing rules (string or JSON-like). Default empty."
)
@click.option(
    "--show",
    default="",
    help="Show output: snippet, template, result."
)
@click.option(
    "--save",
    default="",
    help="Save output to a file (default empty)."
)
@click.option(
    "--config",
    default=None,
    type=click.Path(exists=True),
    help="JSON config file (optional)."
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Print resolved parameters and input metadata."
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Simulate actions without writing files."
)
@click.pass_context
def category(
    ctx,
    input_file,
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
    dry_run
):
    if not input_file and not cmd and config is None:
        click.echo(ctx.get_help())
        return 0

    config_data = {}
    if config:
        required_params = [
            "count",
            "separator",
            "starting_from",
            "ending_at",
            "replacing_rules",
        ]
        status = validate_config(config, required_params)
        if not status:
            emit_status(status)
            return 1
        config_data = status.raw or {}

    input_file_ = merge(input_file, config_data, "input_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    count_ = merge(count, config_data, "count", 1)
    separator_ = merge(separator, config_data, "separator", ":")
    starting_from_ = merge(starting_from, config_data, "starting_from", None)
    ending_at_ = merge(ending_at, config_data, "ending_at", None)
    replacing_rules_ = merge(replacing_rules, config_data, "replacing_rules", None)

    params = {
        "count": abs(count_) or 1,
        "separator": separator_ or ":",
        "starting_from": starting_from_ or None,
        "ending_at": ending_at_ or None,
        "replacing_rules": replacing_rules_ or None,
    }

    if not input_file_ and not cmd_:
        emit_status(
            StatusString(
                "Either input_file or command must be provided",
                status=False,
                reason="warning",
            )
        )
        return 1

    return run_builder_workflow(
        CategoryTemplateBuilder,
        input_file_,
        cmd_,
        params,
        save_,
        show_,
        config,
        debug,
        dry_run,
    )
