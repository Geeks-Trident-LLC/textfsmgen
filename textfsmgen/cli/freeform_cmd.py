import click

from textfsmgen.libs.common import emit_status
from textfsmgen.core.builder import FreeFormBuilder

from textfsmgen.cli.shared_builder_cli import (
    merge,
    validate_config,
    run_builder_workflow,
    generate_or_save_config,
    dry_run_or_create_golden_test,
)

from .json_model import JsonWorkflow


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
@click.option(
    "--create-config",
    is_flag=True,
    default=False,
    help="Preview the generated config (dry run). Prints config to console.",
)
@click.option(
    "--create-config-file",
    default=None,
    type=click.Path(dir_okay=False, writable=True, allow_dash=True),
    help="Generate the config and save it to the specified file.",
)
@click.option(
    "--create-golden-test",
    is_flag=True,
    default=False,
    help="Preview golden test creation (dry run). Shows which files would be created.",
)
@click.option(
    "--create-golden-test-path",
    default=None,
    type=click.Path(dir_okay=True, writable=True, allow_dash=True),
    help="Create a golden test at the specified path under tests/golden/integration/.",
)
@click.option(
    "--json",
    "json_mode",
    is_flag=True,
    default=False,
    help="Output machine-readable JSON instead of human text.",
)
@click.pass_context
def freeform(
    ctx,
    snippet,
    snippet_file,
    sample_file,
    cmd,
    save,
    show,
    config,
    debug,
    dry_run,
    create_config,
    create_config_file,
    create_golden_test,
    create_golden_test_path,
    json_mode,
):
    """
    Build a template from free-form snippet text.
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
    if not snippet and not snippet_file and config is None:
        if json_workflow:
            json_workflow.set_status(
                kind="warning",
                message="Required --snippet, --snippet-file, or --config",
                exit_code=1,
            )
            click.echo(json_workflow.to_json())
            raise SystemExit(1)

        click.echo(ctx.get_help())
        raise SystemExit(0)

    # ------------------------------------------------------------
    # Load config (optional)
    # ------------------------------------------------------------
    config_data = {}
    if config:
        required_top = [
            "builder",
            "params",
            "snippet",
            "snippet_file",
            "sample_file",
            "command",
            "show",
            "save",
        ]
        status = validate_config(config, required_top, [])
        if not status:
            if json_workflow:
                json_workflow.set_status(
                    kind=status.reason,
                    message=str(status),
                    exit_code=1,
                )
                click.echo(json_workflow.to_json())
                raise SystemExit(1)
            emit_status(status)
            raise SystemExit(1)

        config_data = status.raw or {}

    # ------------------------------------------------------------
    # Merge CLI + config
    # ------------------------------------------------------------
    snippet_ = merge(snippet, config_data, "snippet", "")
    snippet_file_ = merge(snippet_file, config_data, "snippet_file", "")
    sample_file_ = merge(sample_file, config_data, "sample_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    params = {}

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
        suppressed_message=suppressed,
        json_workflow=json_workflow,
    )

    # ------------------------------------------------------------
    # Post-build: generate config
    # ------------------------------------------------------------
    if want_config and exit_code == 0:
        generate_or_save_config(
            "freeform",
            cfg_path=create_config_file,
            params=params,
            snippet=snippet_,
            snippet_file=snippet_file_,
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
            FreeFormBuilder,
            "freeform",
            golden_path=create_golden_test_path,
            params=params,
            snippet=snippet_,
            snippet_file=snippet_file_,
            sample_file=sample_file_,
            command=cmd_,
            json_workflow=json_workflow,
        )

    # ------------------------------------------------------------
    # Final JSON output
    # ------------------------------------------------------------
    if json_workflow:
        click.echo(json_workflow.to_json())

    raise SystemExit(exit_code)
