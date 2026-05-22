# workflow_steps.py

import json
from functools import wraps
import time

from textfsmgen.cli.shared_builder_cli import (
    build_debug_report,
    execute_builder,
    create_golden_test,
    create_config,
    save_outputs,
    show_outputs,
)

from textfsmgen.libs.common import emit_status
from textfsmgen.libs.generic import StatusString, DotDict

from textfsmgen.cli import validator
from textfsmgen.cli import parameters


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def abort(state, status_obj, exit_code, *, include_debug=True, **kwargs):
    """Standardized abort handler."""
    message = emit_status(status_obj, display=False)
    debug = (
        state.debug_report if include_debug and hasattr(state, "debug_report") else ""
    )
    output = f"{debug}\n{message}".strip()

    state.update(
        status="aborted", message=message, output=output, exit_code=exit_code, **kwargs
    )
    return state


def complete(state, name, output, exit_code=0, **extra):
    """Standardized completion handler."""
    state.update(
        name=name,
        status="completed",
        message="",
        output=output.strip(),
        exit_code=exit_code,
        **extra,
    )
    return state


def ready_check(func):
    """Skip execution if a previous step has aborted."""

    @wraps(func)
    def wrapper(state):
        if state.status:  # already aborted
            return state
        return func(state)

    return wrapper


def timed_step(func):
    """
    Decorator that measures execution time of each workflow step.
    Stores timing info in state.workflow_steps (list of dicts).
    """

    def wrapper(state):
        start = time.perf_counter()
        new_state = func(state)
        end = time.perf_counter()

        duration_ms = int((end - start) * 1000)

        if "workflow_steps" not in new_state:
            new_state["workflow_steps"] = []

        existed = any(
            step.step == new_state.name for step in new_state["workflow_steps"]
        )

        if not existed:
            new_state["workflow_steps"].append(
                DotDict(
                    {
                        "step": new_state.name,
                        "duration_ms": duration_ms,
                        "status": new_state.status or "completed",
                    }
                )
            )

        return new_state

    return wrapper


# ------------------------------------------------------------
# Steps
# ------------------------------------------------------------
@timed_step
@ready_check
def check_mandatory_cli_options_step(state):
    state.name = "check-mandatory-cli-options"
    o = state.cli_options

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

    if missing:
        return abort(state, status, exit_code=1)

    return state


@timed_step
@ready_check
def load_config_step(state):
    state.name = "load-config"

    if not state.cli_options.config:
        state.loaded_config = DotDict()
        return state

    result = validator.validate_config(state.cli_options.config)
    if not result:
        return abort(
            state,
            result,
            exit_code=2 if result.reason == "code-error" else 1,
            include_debug=False,
        )

    state.loaded_config = DotDict(result.raw)
    return state


@timed_step
@ready_check
def prepare_params_step(state):
    state.name = "prepare-run-params"

    result = parameters.prepare_params(
        state.builder, state.cli_options, state.loaded_config
    )
    if not result:
        return abort(
            state, StatusString(result.message, False, result.reason), result.exit_code
        )

    state.api_params = result.options
    return state


@timed_step
@ready_check
def build_debug_report_step(state):
    state.name = "create-debug-report"
    state.debug_report = build_debug_report(state.api_params)
    state.output = state.debug_report
    return state


@timed_step
@ready_check
def execute_step(state):
    state.name = "execute"

    result = execute_builder(state.api_params)
    state.builder_result = result.builder_result

    if result.exit_code != 0:
        return abort(state, result.status, result.exit_code)

    return state


@timed_step
@ready_check
def create_golden_test_step(state):
    if not state.api_params.create_golden_test:
        return state

    state.name = "create-golden-test"
    result = create_golden_test(state.api_params, state.builder_result)

    if result.exit_code != 0:
        return abort(
            state, result.status, result.exit_code, golden_test=result.creation_result
        )

    output = f"{state.debug_report}\n{result.output}".strip()
    return complete(
        state,
        "create-golden-test",
        output,
        exit_code=result.exit_code,
        golden_test=result.creation_result,
    )


@timed_step
@ready_check
def create_config_step(state):
    if not state.api_params.create_config:
        return state

    state.name = "create-config"
    result = create_config(state.api_params)

    if result.exit_code != 0:
        return abort(
            state,
            result.status,
            result.exit_code,
            generated_config=result.generated_config,
        )

    payload_txt = json.dumps(result.generated_config.payload, indent=2)
    output = (
        f"{state.debug_report}\n{payload_txt}"
        if state.api_params.dry_run
        else f"{state.debug_report}\n{emit_status(result.status, display=False)}"
    ).strip()

    return complete(
        state,
        "create-config",
        output,
        exit_code=result.exit_code,
        generated_config=result.generated_config,
    )


@timed_step
@ready_check
def save_step(state):
    if not state.api_params.save:
        return state

    state.name = "save-output"
    result = save_outputs(state.api_params, state.builder_result)

    if result.exit_code != 0:
        return abort(state, result.status, result.exit_code)

    output = "\n".join(item["message"] for item in result.save_info.files)
    output = f"{state.debug_report}\n{output}"

    return complete(
        state,
        "save-output",
        output,
        exit_code=result.exit_code,
        save=result.save_info,
    )


@timed_step
@ready_check
def show_step(state):
    state.name = "show-output"

    result = show_outputs(state.api_params, state.builder_result)

    if result.exit_code != 0:
        return abort(state, result.status, result.exit_code)

    parts = []
    for item in result.show_info.resolved.values():
        parts.append(item if isinstance(item, str) else json.dumps(item, indent=2))

    output = f"{state.debug_report}\n" + "\n" + ("-" * 60 + "\n").join(parts)

    return complete(
        state,
        "show-output",
        output,
        exit_code=result.exit_code,
        show=result.show_info,
    )
