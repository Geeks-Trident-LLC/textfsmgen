# textfsmgen/core/case_runner.py

import os
from textfsmgen.core.case_loader import CaseLoader
from textfsmgen.core.case_regenerator import CaseRegenerator
from textfsmgen import parse_textfsm_to_dicts


class CaseRunner:
    """
    Executes main or integration golden tests.
    Handles GOLDEN_REGEN logic (regen instead of run).
    """

    def __init__(self, loader: CaseLoader):
        self.loader = loader

    def run(self):
        # ------------------------------------------------------------------
        # GOLDEN_REGEN mode: regenerate instead of running tests
        # ------------------------------------------------------------------
        if os.getenv("GOLDEN_REGEN"):
            CaseRegenerator(self.loader).regenerate()
            return

        # ------------------------------------------------------------------
        # Normal test execution
        # ------------------------------------------------------------------
        return self.run_main() if self.loader.kind == "main" else self.run_integration()

    # ----------------------------------------------------------------------
    # Main golden tests
    # ----------------------------------------------------------------------

    def run_main(self):
        template = self.loader.canonical_template

        for inp, res in self.loader.iter_input_result_pairs():
            parsed = parse_textfsm_to_dicts(template, inp.data)
            assert parsed == res.data, (
                f"Mismatch (canonical template)\n  - {inp.path}\n  - {res.path}"
            )

    # ----------------------------------------------------------------------
    # Integration golden tests
    # ----------------------------------------------------------------------

    def run_integration(self):
        template = self.loader.expected_template

        for inp, res in self.loader.iter_input_result_pairs():
            parsed = parse_textfsm_to_dicts(template, inp.data)
            assert parsed == res.data, (
                f"Mismatch (expected template)\n  - {inp.path}\n  - {res.path}"
            )
