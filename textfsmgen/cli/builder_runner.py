# builder_runner.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


JsonState = Dict[str, Any]
CliParams = Dict[str, Any]


@dataclass
class BuilderRunner:
    """
    Orchestrates the standard builder workflow for:
      - freeform
      - category
      - tabular

    It does NOT know CLI or Click directly.
    It only knows:
      - cli params (already parsed)
      - which builder kind is being run
      - a set of step functions you already have
    """

    builder_kind: str
    cli: CliParams

    # step functions (you plug in your existing helpers)
    init_workflow: Callable[[CliParams], JsonState]
    load_config_step: Callable[[JsonState], JsonState]
    merge_cli_and_config_step: Callable[[JsonState], JsonState]
    determine_post_actions_step: Callable[[JsonState], JsonState]
    run_builder_workflow_step: Callable[[JsonState], JsonState]
    post_build_config_step: Callable[[JsonState], JsonState]
    post_build_golden_test_step: Callable[[JsonState], JsonState]
    finalize_json_output_step: Callable[[JsonState], JsonState]

    # internal state
    state: JsonState = field(default_factory=dict)

    def run(self) -> JsonState:
        """
        Execute the full 9-step workflow and return the final state.
        This is the only method your commands need to call.
        """

        # 1) JSON workflow initialization
        self.state = self.init_workflow(self._with_kind(self.cli))

        # 2) Early help is handled by Click before we get here

        # 3) Load config (optional)
        self.state = self.load_config_step(self.state)

        # 4) Merge CLI + config
        self.state = self.merge_cli_and_config_step(self.state)

        # 5) Determine post-build actions
        self.state = self.determine_post_actions_step(self.state)

        # 6) Run builder workflow
        self.state = self.run_builder_workflow_step(self.state)

        # 7) Post-build: generate config
        self.state = self.post_build_config_step(self.state)

        # 8) Post-build: golden test
        self.state = self.post_build_golden_test_step(self.state)

        # 9) Final JSON output
        self.state = self.finalize_json_output_step(self.state)

        return self.state

    # ------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------

    def _with_kind(self, cli: CliParams) -> CliParams:
        # small helper so your existing init_workflow can see builder_kind
        merged = dict(cli)
        merged.setdefault("builder_kind", self.builder_kind)
        return merged

    # def finalize_workflow(self) -> JsonWorkflow:
    #     """
    #     Construct the final JsonWorkflow object from the internal state.
    #     This is called once after all workflow steps have completed.
    #     """
    #
    #     # Build the JsonState block (your 4-field minimal state)
    #     json_state = JsonState(
    #         name=self.state.get("name", ""),
    #         status=self.state.get("status", ""),
    #         message=self.state.get("message", ""),
    #         output=self.state.get("output", {}) or {},
    #     )
    #
    #     # Construct the full workflow model
    #     workflow = JsonWorkflow(
    #         cli_options=self.state.get("cli_options"),
    #         builder=self.state.get("builder"),
    #         generated_config=self.state.get("generated_config"),
    #         golden_test=self.state.get("golden_test"),
    #         golden_test_dry_run=self.state.get("golden_test_dry_run"),
    #         debug=self.state.get("debug"),
    #         status=self.state.get("status_section"),
    #         state=json_state,
    #     )
    #
    #     return workflow
