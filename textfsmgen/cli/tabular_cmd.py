# textfsmgen/cli/tabular_cmd.py

import click

from textfsmgen.libs.common import emit_status

from textfsmgen import TabularBuilder
from .shared_builder_cli import (
    merge,
    validate_config,
    run_builder_workflow,
    generate_or_save_config,
    dry_run_or_create_golden_test,
)

from .json_model import JsonWorkflow
from .help_text import HELP


def register(cli):
    cli.add_command(tabular)


@click.command(
    help="Generate a TextFSM template from a tabular text sample.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
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
    "--has-header",
    is_flag=True,
    default=True,
    help="Indicates whether the table contains a header row.",
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
def tabular(
    ctx,
    sample_file,
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
    create_config,
    create_config_file,
    create_golden_test,
    create_golden_test_path,
    json_mode,
):
    """
    Build a template from tabular text.
    """

    # ------------------------------------------------------------
    # JSON workflow initialization
    # ------------------------------------------------------------
    json_workflow = JsonWorkflow() if json_mode else None
    if json_workflow:
        json_workflow.add_cli_options(ctx.params.copy())

    # ------------------------------------------------------------
    # Early help
    # ------------------------------------------------------------
    if not sample_file and not cmd and config is None:
        if json_workflow:
            json_workflow.set_status(
                kind="warning",
                message="Required --sample-file, --command, or --config",
                exit_code=1,
            )
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)

        click.echo(ctx.get_help())
        raise SystemExit(0)

    # ------------------------------------------------------------
    # Load config (optional)
    # ------------------------------------------------------------
    config_data = {}
    if config:
        required_top = ["builder", "params", "sample_file", "command", "show", "save"]
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

        status = validate_config(config, required_top, required_params)
        if not status:
            if json_workflow:
                json_workflow.set_status(
                    kind=status.reason,
                    message=str(status),
                    exit_code=1,
                )
                click.echo(json_workflow.to_json(validating=True))
                raise SystemExit(1)

            emit_status(status)
            raise SystemExit(1)

        config_data = status.raw or {}

    # ------------------------------------------------------------
    # Merge CLI + config
    # ------------------------------------------------------------
    sample_file_ = merge(sample_file, config_data, "sample_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    params = {
        "column_divider": merge(column_divider, config_data, "column_divider", ""),
        "column_count": merge(column_count, config_data, "column_count", 0),
        "column_widths": merge(column_widths, config_data, "column_widths", None),
        "headers": merge(headers, config_data, "headers", None),
        "header_rows": merge(header_rows, config_data, "header_rows", None),
        "custom_header_text": merge(
            custom_header, config_data, "custom_header_text", ""
        ),
        "starting_from": merge(starting_from, config_data, "starting_from", None),
        "ending_at": merge(ending_at, config_data, "ending_at", None),
        "has_header_row": merge(has_header, config_data, "has_header_row", True),
        "replacing_rules": merge(replacing_rules, config_data, "replacing_rules", None),
    }

    # ------------------------------------------------------------
    # Determine post-build actions
    # ------------------------------------------------------------
    want_config = create_config or bool(create_config_file)
    want_golden = create_golden_test or bool(create_golden_test_path)
    suppressed = want_config or want_golden

    # ------------------------------------------------------------
    # Run builder workflow
    # ------------------------------------------------------------
    exit_code = run_builder_workflow(
        TabularBuilder,
        sample_file=sample_file_,
        cmd=cmd_,
        params=params,
        save=save_,
        show=show_,
        config=config_data,
        debug=debug,
        suppressed_message=suppressed,
        json_workflow=json_workflow,
    )

    # ------------------------------------------------------------
    # Post-build: generate config
    # ------------------------------------------------------------
    if want_config and exit_code == 0:
        generate_or_save_config(
            "tabular",
            cfg_path=create_config_file,
            params=params,
            sample_file=sample_file_,
            command=cmd_,
            show=show_,
            save=save_,
            json_workflow=json_workflow,
        )

    # ------------------------------------------------------------
    # Post-build: golden test
    # ------------------------------------------------------------
    if want_golden and exit_code == 0:
        dry_run_or_create_golden_test(
            TabularBuilder,
            "tabular",
            golden_path=create_golden_test_path,
            params=params,
            sample_file=sample_file_,
            command=cmd_,
            json_workflow=json_workflow,
        )

    # ------------------------------------------------------------
    # Final JSON output
    # ------------------------------------------------------------
    if json_workflow:
        click.echo(json_workflow.to_json(validating=True))

    raise SystemExit(exit_code)
