# builder_runner.py

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
from .json_model import JsonWorkflow, JsonState


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
        )

    # ------------------------------------------------------------
    # Main runner
    # ------------------------------------------------------------
    def run(self):
        for step in self.WORKFLOW_STEPS:
            self.state = step(self.state)

            if self.state.get("status") == "aborted":
                break

        return self._finalize()

    # ------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------
    def _finalize(self):
        state = self.state
        name = state.get("name", "")
        status = state.get("status", "")

        # ------------------------------------------------------------
        # Golden test handling
        # ------------------------------------------------------------
        golden_test = state.get("golden_test")

        # ------------------------------------------------------------
        # Build JsonWorkflow
        # ------------------------------------------------------------
        workflow = JsonWorkflow(
            cli_options=state.cli_options,
            api_params=state.get("api_params"),
            build_result=state.get("builder_result"),
            debug=state.get("debug_report"),
            golden_test=golden_test,
            generated_config=state.get("generated_config"),
            save=state.get("save"),
            show=state.get("show"),
            state=JsonState(
                name=name,
                status=status,
                message=state.get("message", ""),
                output=state.get("output", {}),
            ),
        )

        # ------------------------------------------------------------
        # Output selection
        # ------------------------------------------------------------
        output = workflow.to_json() if state.cli_options.json_mode else state.output

        return DotDict(output=output, exit_code=state.exit_code)
