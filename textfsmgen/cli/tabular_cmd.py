# textfsmgen/cli/tabular_cmd.py

import click

from textfsmgen.libs.generic import StatusString, emit_status
from textfsmgen import TabularTemplateBuilder

from textfsmgen.cli.shared_builder_cli import (
    merge, validate_config, run_builder_workflow
)


# ------------------------------------------------------------
# CLI Registration
# ------------------------------------------------------------
def register(cli):
    cli.add_command(tabular)


# ------------------------------------------------------------
# Main CLI Command
# ------------------------------------------------------------
@click.command(
    help="Tabular builder for snippet/template/result generation.",
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option("--input-file", default=None, type=click.Path(exists=True))
@click.option("--command", "cmd", default="")
@click.option("--column-divider", default="")
@click.option("--column-count", default=0, type=int)
@click.option("--column-widths", default=None)
@click.option("--headers", default=None)
@click.option("--header-rows", default=None)
@click.option("--custom-header", default="")
@click.option("--starting-from", default=None)
@click.option("--ending-at", default=None)
@click.option("--has-header", is_flag=True, default=True)
@click.option("--replacing-rules", default=None)
@click.option("--show", default="")
@click.option("--save", default="")
@click.option("--config", default=None, type=click.Path(exists=True))
@click.option("--debug", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.pass_context
def tabular(
    ctx,
    input_file,
    cmd,
    column_divider,
    column_count,
    column_widths,
    headers,
    header_rows,
    custom_header,
    starting_from,
    ending_at,
    has_header,
    replacing_rules,
    show,
    save,
    config,
    debug,
    dry_run,
):
    # ------------------------------------------------------------
    # Show help if nothing provided
    # ------------------------------------------------------------
    if not input_file and not cmd and config is None:
        click.echo(ctx.get_help())
        return 0

    # ------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------
    config_data = {}
    if config:
        required_params = [
            "column_divider",
            "column_count",
            "column_widths",
            "headers",
            "header_rows",
            "custom_header_text",
            "starting_from",
            "ending_at",
            "has_header_row",
            "replacing_rules",
        ]
        status = validate_config(config, required_params)
        if not status:
            emit_status(status)
            return 1
        config_data = status.raw or {}

    # ------------------------------------------------------------
    # Merge CLI + config
    # ------------------------------------------------------------
    input_file_ = merge(input_file, config_data, "input_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    params = {
        "column_divider": merge(column_divider, config_data, "column_divider", ""),
        "column_count": merge(column_count, config_data, "column_count", 0),
        "column_widths": merge(column_widths, config_data, "column_widths", None),
        "headers": merge(headers, config_data, "headers", None),
        "header_rows": merge(header_rows, config_data, "header_rows", None),
        "custom_header_text": merge(custom_header, config_data, "custom_header_text", ""),
        "starting_from": merge(starting_from, config_data, "starting_from", None),
        "ending_at": merge(ending_at, config_data, "ending_at", None),
        "has_header_row": merge(has_header, config_data, "has_header_row", True),
        "replacing_rules": merge(replacing_rules, config_data, "replacing_rules", None),
    }

    # ------------------------------------------------------------
    # Must have input_file or cmd
    # ------------------------------------------------------------
    if not input_file_ and not cmd_:
        emit_status(StatusString(
            "Either input_file or command must be provided",
            status=False, reason="warning"
        ))
        return 1

    return run_builder_workflow(
        TabularTemplateBuilder,
        input_file_,
        cmd_,
        params,
        save_,
        show_,
        config,
        debug,
        dry_run,
    )