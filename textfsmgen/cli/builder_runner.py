# builder_runner.py

from textfsmgen.libs.generic import DotDict

from .workflow_steps import (
    check_mandatory_cli_options,
    load_config,
    prepare_run_params,
    create_debug_report,
)

from .json_model import (
    JsonWorkflow,
    JsonState
)


class BuilderRunner:
    def __init__(self, builder="",  usage="", cli_options=None):
        self.state = DotDict({
            "builder": builder,
            "cli_options": DotDict(cli_options),
            "usage": usage,

            "name": "",
            "status": "",
            "message": "",
            "output": "",
            "exit_code": 0

        })

        self.steps = [
            check_mandatory_cli_options,
            load_config,
            prepare_run_params,
            create_debug_report,
            # finalize_json_output_step,
        ]

    def run(self):
        for step in self.steps:
            self.state = step(self.state)

            # abort handling
            if self.state.get("status") == "abort":
                break

        return self.finalize_workflow()

    def finalize_workflow(self):
        workflow = JsonWorkflow(
            cli_options=self.state.get("cli_options"),
            builder=self.state.get("builder_output"),
            generated_config=self.state.get("merged_config"),
            state=JsonState(
                name=self.state.get("name", ""),
                status=self.state.get("status", ""),
                message=self.state.get("message", ""),
                output=self.state.get("output", {}),
            ),
        )

        output = (
            workflow.to_json()
            if self.state.cli_options.json_mode else
            self.state.output
        )
        return DotDict({"output": output, "exit_code": self.state.exit_code})
