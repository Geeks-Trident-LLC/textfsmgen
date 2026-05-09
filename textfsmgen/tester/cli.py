"""
Unified CLI dispatcher for the tester subsystem.

This module handles commands of the form:

    textfsmgen tester <action> <case>

Each action must accept exactly ONE case. If the user passes
multiple cases, this dispatcher raises a clear error.

All heavy logic lives in textfsmgen/tester/commands/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .commands import (
    run as cmd_run,
    regen as cmd_regen,
    diff as cmd_diff,
    drift as cmd_drift,
    preview as cmd_preview,
    quicktest as cmd_quicktest,
    copy as cmd_copy,
    duplicate as cmd_duplicate,
)


class TesterCLI:
    """
    Unified CLI for the tester subsystem.

    Usage:
        textfsmgen tester run <case>
        textfsmgen tester regen <case>
        textfsmgen tester diff <case>
        textfsmgen tester drift <case>
        textfsmgen tester preview <case>
        textfsmgen tester quicktest <case>
        textfsmgen tester copy <case>
        textfsmgen tester duplicate <case>
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def run_from_argv(self, argv: list[str]) -> int:
        parser = self._build_parser()
        args = parser.parse_args(argv)

        if not hasattr(args, "func"):
            parser.print_help()
            return 1

        # Enforce exactly one case
        if args.case is None:
            print("ERROR: Missing <case> argument.")
            return 1

        if isinstance(args.case, list) and len(args.case) != 1:
            print(
                "ERROR: This action accepts exactly one case.\n"
                "If you want to process multiple cases, use a batch action."
            )
            return 1

        case_path = Path(args.case[0]).resolve()
        return args.func(case_path)

    # ------------------------------------------------------------------
    # Parser construction
    # ------------------------------------------------------------------
    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="textfsmgen tester",
            description="Golden test utilities",
            add_help=True,
        )

        subparsers = parser.add_subparsers(
            dest="action",
            metavar="<action>",
        )

        # --------------------------------------------------------------
        # run
        # --------------------------------------------------------------
        p_run = subparsers.add_parser(
            "run",
            help="Run a golden test case (non-destructive).",
        )
        p_run.add_argument("case", nargs=1, help="Path to test case directory.")
        p_run.set_defaults(func=self._dispatch_run)

        # --------------------------------------------------------------
        # regen
        # --------------------------------------------------------------
        p_regen = subparsers.add_parser(
            "regen",
            help="Regenerate meta.json and golden.hash for a case.",
        )
        p_regen.add_argument("case", nargs=1, help="Path to test case directory.")
        p_regen.set_defaults(func=self._dispatch_regen)

        # --------------------------------------------------------------
        # diff
        # --------------------------------------------------------------
        p_diff = subparsers.add_parser(
            "diff",
            help="Show differences between expected and actual results.",
        )
        p_diff.add_argument("case", nargs=1, help="Path to test case directory.")
        p_diff.set_defaults(func=self._dispatch_diff)

        # --------------------------------------------------------------
        # drift
        # --------------------------------------------------------------
        p_drift = subparsers.add_parser(
            "drift",
            help="Detect drift between canonical and expected results.",
        )
        p_drift.add_argument("case", nargs=1, help="Path to test case directory.")
        p_drift.set_defaults(func=self._dispatch_drift)

        # --------------------------------------------------------------
        # preview
        # --------------------------------------------------------------
        p_preview = subparsers.add_parser(
            "preview",
            help="Preview parsing results for a case.",
        )
        p_preview.add_argument("case", nargs=1, help="Path to test case directory.")
        p_preview.set_defaults(func=self._dispatch_preview)

        # --------------------------------------------------------------
        # quicktest
        # --------------------------------------------------------------
        p_quick = subparsers.add_parser(
            "quicktest",
            help="Run a quick test without writing any files.",
        )
        p_quick.add_argument("case", nargs=1, help="Path to test case directory.")
        p_quick.set_defaults(func=self._dispatch_quicktest)

        # --------------------------------------------------------------
        # copy
        # --------------------------------------------------------------
        p_copy = subparsers.add_parser(
            "copy",
            help="Copy a golden test case to a new location.",
        )
        p_copy.add_argument("case", nargs=1, help="Path to test case directory.")
        p_copy.set_defaults(func=self._dispatch_copy)

        # --------------------------------------------------------------
        # duplicate
        # --------------------------------------------------------------
        p_dup = subparsers.add_parser(
            "duplicate",
            help="Duplicate a golden test case.",
        )
        p_dup.add_argument("case", nargs=1, help="Path to test case directory.")
        p_dup.set_defaults(func=self._dispatch_duplicate)

        return parser

    # ------------------------------------------------------------------
    # Dispatchers
    # ------------------------------------------------------------------
    def _dispatch_run(self, case_path: Path) -> int:
        return cmd_run.run(case_path)

    def _dispatch_regen(self, case_path: Path) -> int:
        return cmd_regen.regen(case_path)

    def _dispatch_diff(self, case_path: Path) -> int:
        return cmd_diff.diff(case_path)

    def _dispatch_drift(self, case_path: Path) -> int:
        return cmd_drift.drift(case_path)

    def _dispatch_preview(self, case_path: Path) -> int:
        return cmd_preview.preview(case_path)

    def _dispatch_quicktest(self, case_path: Path) -> int:
        return cmd_quicktest.quicktest(case_path)

    def _dispatch_copy(self, case_path: Path) -> int:
        return cmd_copy.copy_case(case_path)

    def _dispatch_duplicate(self, case_path: Path) -> int:
        return cmd_duplicate.duplicate(case_path)
