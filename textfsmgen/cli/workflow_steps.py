# workflow_steps.py

from functools import wraps

from textfsmgen.cli.shared_builder_cli import (
    merge,
    run_builder_workflow,
    generate_or_save_config,
    dry_run_or_create_golden_test,

    run_builder_workflow_new,
    generate_or_save_config_new,
    dry_run_or_create_golden_test_new,
)

from textfsmgen.libs.common import emit_status
from textfsmgen.libs.generic import StatusString, DotDict

from textfsmgen.cli import validator
from textfsmgen.cli.parameters import prepare_params


def ready_check(func):
    """Skip execution if a previous step has aborted."""
    @wraps(func)
    def wrapper(state):
        if hasattr(state, "status") and state.status:
            return state
        return func(state)
    return wrapper


@ready_check
def check_mandatory_cli_options(state):
    state.name = "check-mandatory-cli-options"
    o = state.cli_options

    # Determine required fields based on builder type
    if state.builder == "freeform":
        missing = not o.snippet and not o.snippet_file and o.config is None
        status = StatusString(
            "missing required option: --snippet, --snippet-file, or --config",
            status=False,
            reason="error"
        )
    else:
        missing = not o.sample_file and not o.command and o.config is None
        status = StatusString(
            "missing required option: --sample-file, --command, or --config",
            status=False,
            reason="error"
        )

    # Abort if mandatory options missing
    if missing:
        state.update(
            status="abort",
            message=emit_status(status, display=False),
            output=f"{state.message}\n{state.usage}",
            exit_code=1,
        )
        return state

    return state


@ready_check
def load_config(state):
    state.name = "load-config"
    if not state.cli_options.config:
        state.loaded_config = DotDict()
        return state

    result = validator.validate_config(state.cli_options.config)
    if not result:
        state.update(
            status="abort",
            message=emit_status(result, display=False),
            output=emit_status(result, display=False),
            exit_code=2 if result.reason == "code-error" else 1
        )
        return state

    state.loaded_config = DotDict(result.raw)
    return state


@ready_check
def prepare_run_params(state):
    state.name = "prepare-run-params"
    result = prepare_params(state.builder, state.cli_options, state.loaded_config)
    if not result:
        state.update(
            status="abort",
            message=result.message,
            output=result.message,
            exit_code=result.exit_code,
        )
        return state

    state.api_params = result.options
    return state

