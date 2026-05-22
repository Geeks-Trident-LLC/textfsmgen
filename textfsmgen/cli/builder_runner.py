# builder_runner.py

import time
from datetime import datetime, timezone

from textfsmgen.libs.generic import DotDict
from .workflow_steps import (
    check_mandatory_cli_options_step,
    load_config_step,
    prepare_params_step,
    build_debug_report_step,
    execute_step,
    create_golden_test_step,
    create_config_step,
    save_step,
    show_step,
)
from .json_model import JsonWorkflow, JsonState, ErrorInfo

import textfsmgen


class BuilderRunner:
    """
    Executes a sequence of workflow steps and produces a JsonWorkflow summary.
    """

    WORKFLOW_STEPS = [
        check_mandatory_cli_options_step,
        load_config_step,
        prepare_params_step,
        build_debug_report_step,
        execute_step,
        create_golden_test_step,
        create_config_step,
        save_step,
        show_step,
    ]

    def __init__(self, builder="", usage="", cli_options=None):
        self.state = DotDict(
            builder=builder,
            cli_options=DotDict(cli_options),
            usage=usage,
            name="",
            status="",
            message="",
            output="",
            exit_code=0,
            workflow_steps=[],
        )
        self._start_timestamp = ""
        self._duration_ms = 0

    # ------------------------------------------------------------
    # Main runner
    # ------------------------------------------------------------
    def run(self):
        start = time.perf_counter()
        self._start_timestamp = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )

        for step in self.WORKFLOW_STEPS:
            self.state = step(self.state)
            if self.state.get("status") == "aborted":
                break

        self._duration_ms = int((time.perf_counter() - start) * 1000)
        return self._finalize()

    # ------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------
    def _finalize(self):
        state = self.state
        name = state.get("name", "")
        status = state.get("status", "")

        # ------------------------------------------------------------
        # Build JsonWorkflow
        # ------------------------------------------------------------
        workflow = JsonWorkflow(
            cli_options=state.cli_options,
            api_params=state.get("api_params"),
            build_result=state.get("builder_result"),
            debug=state.get("debug_report"),
            golden_test=state.get("golden_test"),
            generated_config=state.get("generated_config"),
            save=state.get("save"),
            show=state.get("show"),
            state=JsonState(
                name=name,
                status=status,
                message=state.get("message", ""),
                output=state.get("output", {}),
            ),
            steps=state.get("workflow_steps"),
        )

        # ------------------------------------------------------------
        # Populate meta
        # ------------------------------------------------------------
        workflow.meta.workflow_version = "1.0"
        workflow.meta.builder_version = getattr(textfsmgen, "__version__", None)
        workflow.meta.timestamp = self._start_timestamp
        workflow.meta.duration_ms = self._duration_ms

        # ------------------------------------------------------------
        # Populate artifacts
        # ------------------------------------------------------------
        if state.get("generated_config"):
            workflow.artifacts.config = state.generated_config.path

        if state.get("golden_test"):
            workflow.artifacts.golden_test = state.golden_test.path

        if state.get("save"):
            workflow.artifacts.save_files = [
                f["path"] for f in state.save.files if f.get("path")
            ]

        if state.get("show"):
            workflow.artifacts.show_outputs = list(state.show.resolved.keys())

        # ------------------------------------------------------------
        # Populate error (only if aborted)
        # ------------------------------------------------------------
        if status == "aborted":
            workflow.error = ErrorInfo(
                type="workflow-error",
                code=name,
                fatal=True,
                details=state.get("message", ""),
            )

        # ------------------------------------------------------------
        # Output selection
        # ------------------------------------------------------------
        output = workflow.to_json() if state.cli_options.json_mode else state.output

        return DotDict(output=output, exit_code=state.exit_code)
