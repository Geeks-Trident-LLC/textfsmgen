# workflow_steps.py
import copy
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


def create_step(index, name):
    return DotDict(
        index=index,
        name=name,
        duration_ms=0,
        status="pending",
        skipped=True,
        reason=None,
    )


STEP_NAMES = [
    "check-mandatory-cli-options",
    "load-config",
    "prepare-run-params",
    "build-debug-report",
    "execute",
    "create-golden-test",
    "create-config",
    "save-outputs",
    "show-outputs",
]

WORKFLOW_STEPS = [create_step(i, name) for i, name in enumerate(STEP_NAMES)]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def abort(state, status_obj, exit_code, *, include_debug=True, **extra):
    """Standardized abort handler."""
    message = emit_status(status_obj, display=False)
    debug = (
        state.debug_report if include_debug and hasattr(state, "debug_report") else ""
    )
    output = f"{debug}\n{message}".strip()

    state.update(
        status="aborted", message=message, output=output, exit_code=exit_code, **extra
    )
    return state


def complete(state, output, exit_code=0, **extra):
    """Standardized completion handler."""
    state.update(
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
        state.step_name = func.__name__.replace("_step", "").replace("_", "-")
        if state.status:  # aborted or completed
            return state

        state.step_skipped = False
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
            new_state.workflow_steps = copy.deepcopy(WORKFLOW_STEPS)

        step = None

        for i in state.workflow_steps:
            if i.name == new_state.step_name:
                step = i
                break

        if step is not None:
            step.duration_ms = duration_ms
            step.status = new_state.status or "complete"
            step.skipped = new_state.step_skipped
            step.reason = new_state.message

        return new_state

    return wrapper


# ------------------------------------------------------------
# Finalize helpers
# ------------------------------------------------------------


def build_step_summary(steps, state):
    total_steps = len(steps)
    skipped_steps = sum(1 for s in steps if s.get("skipped"))
    executed_steps = total_steps - skipped_steps

    aborted = state.get("status") == "aborted"

    failed_step = None
    if aborted:
        for s in reversed(steps):
            if not s.get("skipped"):
                failed_step = s["name"]
                break

    longest_step = None
    if steps:
        longest = max(steps, key=lambda s: s.get("duration_ms", 0))
        longest_step = {
            "name": longest["name"],
            "duration_ms": longest["duration_ms"],
        }

    return {
        "total_steps": total_steps,
        "executed_steps": executed_steps,
        "skipped_steps": skipped_steps,
        "aborted": aborted,
        "failed_step": failed_step,
        "longest_step": longest_step,
    }


def finalize_steps(state, start_timestamp, duration_ms):
    """
    Post-process workflow:
    - ensure all steps exist
    - mark skipped steps and reasons
    - compute total_duration_ms
    - compute step_summary
    - attach meta
    """
    # Ensure workflow_steps exists
    if "workflow_steps" not in state:
        state.workflow_steps = copy.deepcopy(WORKFLOW_STEPS)

    steps = state.workflow_steps
    steps_by_name = {s["name"]: s for s in steps}

    # Ensure every static step exists
    for template in WORKFLOW_STEPS:
        if template["name"] not in steps_by_name:
            steps.append(copy.deepcopy(template))

    # Sort by index
    steps.sort(key=lambda s: s["index"])

    # Mark skipped + reason for steps that never ran
    aborted = state.get("status") == "aborted"
    for s in steps:
        if s["status"] == "pending":
            s["skipped"] = True
            s["status"] = "skipped"
            if aborted:
                s["reason"] = "workflow-aborted"
            else:
                s["reason"] = "flag-disabled"

    total_duration_ms = sum(s.get("duration_ms", 0) for s in steps)

    state.step_summary = build_step_summary(steps, state)

    if "meta" not in state:
        state.meta = {}
    state.meta.update(
        workflow_version="1.0",
        builder_version="0.6.3",
        timestamp=start_timestamp,
        duration_ms=duration_ms,
        total_duration_ms=total_duration_ms,
    )

    return state


# ------------------------------------------------------------
# Steps
# ------------------------------------------------------------
@timed_step
@ready_check
def check_mandatory_cli_options_step(state):

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
def prepare_run_params_step(state):

    result = parameters.prepare_params(
        state.builder, state.cli_options, state.loaded_config
    )
    if not result:
        return abort(
            state, StatusString(result.message, False, result.status), result.exit_code
        )

    state.api_params = result.options
    return state


@timed_step
@ready_check
def build_debug_report_step(state):

    state.debug_report = build_debug_report(state.api_params)
    state.output = state.debug_report
    return state


@timed_step
@ready_check
def execute_step(state):

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

    result = create_golden_test(state.api_params, state.builder_result)

    if result.exit_code != 0:
        return abort(
            state, result.status, result.exit_code, golden_test=result.creation_result
        )

    output = f"{state.debug_report}\n{result.output}".strip()
    return complete(
        state,
        output,
        exit_code=result.exit_code,
        golden_test=result.creation_result,
    )


@timed_step
@ready_check
def create_config_step(state):

    if not state.api_params.create_config:
        return state
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
        output,
        exit_code=result.exit_code,
        generated_config=result.generated_config,
    )


@timed_step
@ready_check
def save_outputs_step(state):
    if not state.api_params.save:
        return state

    result = save_outputs(state.api_params, state.builder_result)

    if result.exit_code != 0:
        return abort(state, result.status, result.exit_code)

    output = "\n".join(item["message"] for item in result.save_info.files)
    output = f"{state.debug_report}\n{output}"

    return complete(
        state,
        output,
        exit_code=result.exit_code,
        save=result.save_info,
    )


@timed_step
@ready_check
def show_outputs_step(state):
    result = show_outputs(state.api_params, state.builder_result)

    if result.exit_code != 0:
        return abort(state, result.status, result.exit_code)

    parts = []
    for item in result.show_info.resolved.values():
        parts.append(item if isinstance(item, str) else json.dumps(item, indent=2))

    output = f"{state.debug_report}\n" + "\n" + ("-" * 60 + "\n").join(parts)

    return complete(
        state,
        output,
        exit_code=result.exit_code,
        show=result.show_info,
    )
