"""
Unified CLI dispatcher for the tester subsystem.

This module handles commands of the form:

    textfsmgen tester <action> <args...>

Most actions accept exactly ONE <case> argument.
However, actions like COPY and DUPLICATE accept multiple arguments.

All heavy logic lives in textfsmgen/tester/commands/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .commands import (
    run as cmd_run,
    regen as cmd_regen,
    diff as cmd_diff,
    drift as cmd_drift,
    quicktest as cmd_quicktest,
    copy as cmd_copy,
    duplicate as cmd_duplicate,
    new as cmd_new,
)


class TesterCLI:
    """
    Unified CLI for the tester subsystem.

    Actions:
        run <case>
        regen <case>
        diff <case>
        drift <case>
        quicktest <case>

        copy <author> <src> <dst>
        duplicate <author> <src>
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

        # --------------------------------------------------------------
        # Special-case actions: copy, duplicate
        # These DO NOT use the <case> argument pattern.
        # --------------------------------------------------------------
        if args.action == "copy":
            return self._dispatch_copy(args)

        if args.action == "duplicate":
            return self._dispatch_duplicate(args)

        if args.action == "new":
            return self._dispatch_new(args)

        # --------------------------------------------------------------
        # All other actions require exactly ONE <case>
        # --------------------------------------------------------------
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
        p_run = subparsers.add_parser("run", help="Run a golden test case.")
        p_run.add_argument("case", nargs=1)
        p_run.set_defaults(func=self._dispatch_run)

        # --------------------------------------------------------------
        # regen
        # --------------------------------------------------------------
        p_regen = subparsers.add_parser("regen", help="Regenerate meta + hash.")
        p_regen.add_argument("case", nargs=1)
        p_regen.set_defaults(func=self._dispatch_regen)

        # --------------------------------------------------------------
        # diff
        # --------------------------------------------------------------
        p_diff = subparsers.add_parser("diff", help="Show differences.")
        p_diff.add_argument("case", nargs=1)
        p_diff.set_defaults(func=self._dispatch_diff)

        # --------------------------------------------------------------
        # drift
        # --------------------------------------------------------------
        p_drift = subparsers.add_parser("drift", help="Detect drift.")
        p_drift.add_argument("case", nargs=1)
        p_drift.set_defaults(func=self._dispatch_drift)

        # --------------------------------------------------------------
        # quicktest
        # --------------------------------------------------------------
        p_quick = subparsers.add_parser("quicktest", help="Quick test.")
        p_quick.add_argument("case", nargs=1)
        p_quick.set_defaults(func=self._dispatch_quicktest)

        # --------------------------------------------------------------
        # copy (special: 3 positional args)
        # --------------------------------------------------------------
        p_copy = subparsers.add_parser(
            "copy",
            help="Copy a golden test case into a new case directory.",
        )
        p_copy.add_argument("author", help="Author name for metadata.")
        p_copy.add_argument("src", help="Source case directory.")
        p_copy.add_argument("dst", help="Destination case directory.")
        # NEW FLAGS
        p_copy.add_argument(
            "--dry-run",
            action="store_true",
            help="Copy into <dst>.temp, run quicktest, delete temp on success.",
        )

        p_copy.add_argument(
            "--force",
            action="store_true",
            help="Allow overwriting an existing destination directory.",
        )
        p_copy.set_defaults(func=self._dispatch_copy)

        # --------------------------------------------------------------
        # duplicate (special: 2 positional args)
        # --------------------------------------------------------------
        p_dup = subparsers.add_parser(
            "duplicate",
            help="Duplicate a golden test case into an auto-named sibling directory.",
        )
        p_dup.add_argument("author", help="Author name for metadata.")
        p_dup.add_argument("src", help="Source case directory.")

        # NEW FLAGS
        p_dup.add_argument(
            "--dry-run",
            action="store_true",
            help="Duplicate into <src>_copy.temp, run quicktest, delete temp on success.",
        )

        p_dup.add_argument(
            "--force",
            action="store_true",
            help="Allow overwriting an existing duplicate directory.",
        )

        p_dup.set_defaults(func=self._dispatch_duplicate)

        # --------------------------------------------------------------
        # new
        # --------------------------------------------------------------
        # new
        p_new = subparsers.add_parser(
            "new",
            help="Create a new golden test case scaffold (auto-detect main/integration).",
        )
        p_new.add_argument("case", nargs=1)
        p_new.add_argument(
            "--force",
            action="store_true",
            help="Allow overwriting an existing case directory.",
        )
        p_new.set_defaults(func=self._dispatch_new)

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

    def _dispatch_quicktest(self, case_path: Path) -> int:
        return cmd_quicktest.quicktest(case_path)

    # --------------------------------------------------------------
    # Special-case dispatchers
    # --------------------------------------------------------------
    def _dispatch_copy(self, args) -> int:
        return cmd_copy.copy_case(
            author=args.author,
            src=Path(args.src),
            dst=Path(args.dst),
            dry_run=args.dry_run,
            force=args.force,
        )

    def _dispatch_duplicate(self, args) -> int:
        return cmd_duplicate.duplicate_case(
            author=args.author,
            src=Path(args.src),
            dry_run=args.dry_run,
            force=args.force,
        )

    def _dispatch_new(self, args) -> int:
        case_path = Path(args.case[0]).resolve()

        if case_path.exists() and not args.force:
            print(f"[FAIL] Case directory already exists: {case_path}")
            print("       Use --force to overwrite.")
            return 1

        return cmd_new.new(case_path)

