# workflow_steps.py

import json
from functools import wraps

from textfsmgen.cli.shared_builder_cli import (
    build_debug_report,
    execute_builder,
    create_golden_test,
    create_config,
    save_outputs_v2
)

from textfsmgen.libs.common import emit_status
from textfsmgen.libs.generic import StatusString, DotDict

from textfsmgen.cli import validator
from textfsmgen.cli import parameters


def ready_check(func):
    """Skip execution if a previous step has aborteded."""

    @wraps(func)
    def wrapper(state):
        if hasattr(state, "status") and state.status:
            return state
        return func(state)

    return wrapper


@ready_check
def check_mandatory_cli_options_step(state):
    state.name = "check-mandatory-cli-options"
    o = state.cli_options

    # Determine required fields based on builder type
    if state.builder == "freeform":
        missing = not o.snippet and not o.snippet_file and o.config is None
        status = StatusString(
            "missing required option: --snippet, --snippet-file, or --config",
            status=False,
            reason="error",
        )
    else:
        missing = not o.sample_file and not o.command and o.config is None
        status = StatusString(
            "missing required option: --sample-file, --command, or --config",
            status=False,
            reason="error",
        )

    # Abort if mandatory options missing
    if missing:
        state.update(
            status="aborted",
            message=emit_status(status, display=False),
            output=f"{state.message}\n{state.usage}",
            exit_code=1,
        )
        return state

    return state


@ready_check
def load_config_step(state):
    state.name = "load-config"
    if not state.cli_options.config:
        state.loaded_config = DotDict()
        return state

    result = validator.validate_config(state.cli_options.config)
    if not result:
        state.update(
            status="aborted",
            message=emit_status(result, display=False),
            output=emit_status(result, display=False),
            exit_code=2 if result.reason == "code-error" else 1,
        )
        return state

    state.loaded_config = DotDict(result.raw)
    return state


@ready_check
def prepare_params_step(state):
    state.name = "prepare-run-params"
    result = parameters.prepare_params(
        state.builder, state.cli_options, state.loaded_config
    )
    if not result:
        state.update(
            status="aborted",
            message=result.message,
            output=result.message,
            exit_code=result.exit_code,
        )
        return state

    state.api_params = result.options
    return state


@ready_check
def build_debug_report_step(state):
    state.name = "create-debug-report"
    state.debug_report = build_debug_report(state.api_params)

    state.output = state.debug_report
    return state


@ready_check
def execute_step(state):
    state.name = "execute"
    result = execute_builder(state.api_params)
    state.builder_result = result.builder_result

    message = emit_status(result.status, display=False)

    if result.exit_code != 0:
        state.update(
            status="aborted",
            message=message,
            output=f"{state.debug_report}\n{message}".strip(),
            exit_code=result.exit_code,
        )
        return state

    return state


@ready_check
def create_golden_test_step(state):

    if not state.api_params.create_golden_test and not state.api_params.create_golden_test_path:
        return state

    state.name = "create-golden-test"
    result = create_golden_test(state.api_params, state.builder_result)

    message = emit_status(result.status, display=False)

    if result.exit_code != 0:
        state.update(
            status="aborted",
            message=message,
            output=f"{state.debug_report}\n{message}".strip(),
            exit_code=result.exit_code,
        )
        return state

    state.update(
        golden_test=result.creation_result,
        status="completed",
        message="",
        output=f"{state.debug_report}\n{result.output}".strip(),
        exit_code=result.exit_code,
    )
    return state


@ready_check
def create_config_step(state):

    if not state.api_params.create_config and not state.api_params.create_config_file:
        return state

    state.name = "create-config"
    result = create_config(state.api_params)

    message = emit_status(result.status, display=False)

    payload_txt = json.dumps(result.generated_config.payload, indent=2)

    if result.exit_code != 0:
        state.update(
            status="aborted",
            message=message,
            output=f"{state.debug_report}\n{message}".strip(),
            exit_code=result.exit_code,
        )
        return state

    state.update(
        generated_config=result.generated_config,
        status="completed",
        message="",
        output=(
            f"{state.debug_report}\n{payload_txt}".strip()
            if result.generated_config.stream == "stream" else
            f"{state.debug_report}\n{message}".strip()
        ),
        exit_code=result.exit_code,
    )
    return state


@ready_check
def save_step(state):

    if not state.api_params.save:
        return state

    state.name = "save-output"

    result = save_outputs_v2(state.api_params, state.builder_result)

    message = emit_status(result.status, display=False)

    if result.exit_code != 0:
        state.update(
            status="aborted",
            message=message,
            output=f"{state.debug_report}\n{message}".strip(),
            exit_code=result.exit_code,
        )
        return state

    state.update(
        save=DotDict(raw=state.api_params.save, files=result.files),
        status="completed",
        message="",
        output=(
            f"{state.debug_report}\n{'\n'.join(item['message'] for item in result.files)}".strip()
        ),
        exit_code=result.exit_code,
    )
    return state