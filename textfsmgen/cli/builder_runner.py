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
    show_step
)

from .json_model import JsonWorkflow, JsonState


class BuilderRunner:
    def __init__(self, builder="", usage="", cli_options=None):
        self.state = DotDict(
            {
                "builder": builder,
                "cli_options": DotDict(cli_options),
                "usage": usage,
                "name": "",
                "status": "",
                "message": "",
                "output": "",
                "exit_code": 0,
            }
        )

        self.steps = [
            check_mandatory_cli_options_step,
            load_config_step,
            prepare_params_step,
            build_debug_report_step,
            execute_step,
            create_golden_test_step,
            create_config_step,
            save_step,
            show_step
        ]

    def run(self):
        for step in self.steps:
            self.state = step(self.state)

            # abort handling
            if self.state.get("status") == "aborted":
                break

        return self.finalize_workflow()

    def finalize_workflow(self):
        state = self.state
        state_name = self.state.get("name", "")
        state_status = self.state.get("status", "")

        golden_test = None
        golden_test_dry_run = None
        if state_name == "create-golden-test" and state_status == "completed":
            if state.api_params.create_golden_test_path:
                golden_test = state.get("golden_test", None)
                golden_test_dry_run = []
            else:
                golden_test = None
                golden_test_dry_run = state.output.splitlines()

        workflow = JsonWorkflow(
            cli_options=state.get("cli_options"),
            api_params=state.get("api_params"),
            builder=state.get("builder_output"),
            debug=state.get("debug_report"),
            golden_test=golden_test,
            golden_test_dry_run=golden_test_dry_run,
            generated_config=state.get("generated_config"),
            save=state.get("save"),
            state=JsonState(
                name=state.get("name", ""),
                status=state.get("status", ""),
                message=state.get("message", ""),
                output=state.get("output", {}),
            ),
        )

        output = (
            workflow.to_json()
            if self.state.cli_options.json_mode
            else self.state.output
        )
        return DotDict({"output": output, "exit_code": self.state.exit_code})
