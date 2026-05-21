import click

from textfsmgen.libs.common import emit_status
from textfsmgen.core.builder import FreeFormBuilder

from textfsmgen.cli.shared_builder_cli import (
    merge,
    validate_config,
    run_builder_workflow,
    generate_or_save_config,
    dry_run_or_create_golden_test,

    validate_config_new,
    run_builder,
    generate_or_save_config_new,
    dry_run_or_create_golden_test_new,

)

from .builder_runner import BuilderRunner

from .json_model import JsonWorkflow
from .help_text import HELP


def register(cli):
    cli.add_command(freeform)
    cli.add_command(freeform2)


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
def freeform(ctx, **kwargs):
    """
    Build a template from free-form snippet text.
    """
    snippet = kwargs.get("snippet")
    snippet_file = kwargs.get("snippet_file")
    sample_file = kwargs.get("sample_file")
    command = kwargs.get("command")
    save = kwargs.get("save")
    show = kwargs.get("show")
    config = kwargs.get("config")
    debug = kwargs.get("debug")
    create_config = kwargs.get("create_config")
    create_config_file = kwargs.get("create_config_file")
    create_golden_test = kwargs.get("create_golden_test")
    create_golden_test_path = kwargs.get("create_golden_test_path")
    json_mode = kwargs.get("json_mode")

    # ------------------------------------------------------------
    # JSON workflow initialization
    # ------------------------------------------------------------
    json_workflow = JsonWorkflow() if json_mode else None
    if json_workflow:
        json_workflow.add_cli_options(kwargs.copy())

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
            click.echo(json_workflow.to_json(validating=True))
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
                click.echo(json_workflow.to_json(validating=True))
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
    command_ = merge(command, config_data, "command", "")
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
        command=command_,
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
            "freeform",
            cfg_path=create_config_file,
            params=params,
            snippet=snippet_,
            snippet_file=snippet_file_,
            sample_file=sample_file_,
            command=command_,
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
            command=command_,
            json_workflow=json_workflow,
        )

    # ------------------------------------------------------------
    # Final JSON output
    # ------------------------------------------------------------
    if json_workflow:
        click.echo(json_workflow.to_json(validating=True))

    raise SystemExit(exit_code)



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
def freeform2(ctx, **cli_options):
    runner = BuilderRunner(
        builder="freeform",
        usage=ctx.get_help(),
        cli_options=cli_options
    )

    result = runner.run()

    click.echo(result.output)
    raise SystemExit(result.exit_code)
