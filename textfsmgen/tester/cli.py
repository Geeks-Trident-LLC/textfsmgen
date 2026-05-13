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
import json

from .commands import (
    run as cmd_run,
    regen as cmd_regen,
    diff as cmd_diff,
    drift as cmd_drift,
    quicktest as cmd_quicktest,
    copy as cmd_copy,
    duplicate as cmd_duplicate,
    new as cmd_new,
    new_from_input as cmd_new_from_input,
    generate as cmd_generate,

    batch_generate as cmd_batch_generate,
    batch_regen as cmd_batch_regen,
    batch_quicktest as cmd_batch_quicktest,

    merge as cmd_merge,
    merge_review as cmd_merge_review,
    merge_preview as cmd_merge_preview,
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
        if args.action == "run":
            return self._dispatch_run(args)

        if args.action == "quicktest":
            return self._dispatch_quicktest(args)

        if args.action == "regen":
            return self._dispatch_regen(args)

        if args.action == "copy":
            return self._dispatch_copy(args)

        if args.action == "duplicate":
            return self._dispatch_duplicate(args)

        if args.action == "new":
            return self._dispatch_new(args)

        if args.action == "new-from-input":
            return self._dispatch_new_from_input(args)

        if args.action == "generate":
            return self._dispatch_generate(args)

        if args.action == "batch-generate":
            return self._dispatch_batch_generate(args)

        if args.action == "batch-regen":
            return self._dispatch_batch_regen(args)

        if args.action == "batch-quicktest":
            return self._dispatch_batch_quicktest(args)

        if args.action == "merge":
            return self._dispatch_merge(args)

        if args.action == "merge-review":
            return self._dispatch_merge_review(args)

        if args.action == "merge-preview":
            return self._dispatch_merge_preview(args)

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
        p_run = subparsers.add_parser(
            "run",
            help="Execute a non-destructive test run for a golden test case.",
        )

        p_run.add_argument(
            "--dry-run",
            action="store_true",
            help="Run inside <case>.temp and delete it on success.",
        )

        p_run.add_argument(
            "case",
            nargs=1,
            help="Path to the case directory.",
        )

        p_run.set_defaults(func=self._dispatch_run)

        # --------------------------------------------------------------
        # regen
        # --------------------------------------------------------------
        p_regen = subparsers.add_parser(
            "regen",
            help="Regenerate derived artifacts for a golden test case.",
        )

        p_regen.add_argument(
            "--dry-run",
            action="store_true",
            help="Run regen inside <case>.temp and delete it on success.",
        )

        p_regen.add_argument(
            "case",
            nargs=1,
            help="Path to the case directory.",
        )

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
        p_quick = subparsers.add_parser(
            "quicktest",
            help="Run quicktest for a golden test case.",
        )

        p_quick.add_argument(
            "--dry-run",
            action="store_true",
            help="Run quicktest inside <case>.temp and delete it on success.",
        )

        p_quick.add_argument(
            "case",
            nargs=1,
            help="Path to the case directory.",
        )

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

        # --------------------------------------------------------------
        # new-from-input
        # --------------------------------------------------------------
        p_new_in = subparsers.add_parser(
            "new-from-input",
            help="Create a new integration case from an input folder.",
        )

        p_new_in.add_argument(
            "--builder",
            required=True,
            help="Name of the builder to use for generating snippet/template (required).",
        )

        p_new_in.add_argument(
            "--params",
            default="{}",
            help="JSON object of builder parameters (optional). Example: '{\"normalize\": true}'.",
        )

        p_new_in.add_argument(
            "--author",
            required=True,
            help="Author name recorded in manifest.json (required).",
        )

        p_new_in.add_argument(
            "--force",
            action="store_true",
            help="Overwrite the existing <case> directory if it already exists.",
        )

        p_new_in.add_argument(
            "--accept",
            action="store_true",
            help="Keep the generated <case> even if quicktest fails. Without this flag, "
                 "a failed quicktest deletes the case.",
        )

        p_new_in.add_argument(
            "--dry-run",
            action="store_true",
            help="Create <case>.temp instead of <case>. Run quicktest, then delete the "
                 "temporary directory unless --accept is used.",
        )

        p_new_in.add_argument(
            "case",
            nargs=1,
            help="Target integration case directory (must be under golden/integration).",
        )

        p_new_in.add_argument(
            "inputs",
            nargs=1,
            help="Folder containing input files used to generate expected artifacts.",
        )

        p_new_in.set_defaults(func=self._dispatch_new_from_input)

        # --------------------------------------------------------------
        # generate
        # --------------------------------------------------------------

        p_generate = subparsers.add_parser(
            "generate",
            help="Generate expected artifacts for an existing case using manifest.json and inputs/.",
        )

        p_generate.add_argument(
            "--dry-run",
            action="store_true",
            help="Run generation inside <case>.temp and delete it on success.",
        )

        p_generate.add_argument(
            "case",
            nargs=1,
            help="Path to an existing case directory (must contain manifest.json and inputs/).",
        )

        p_generate.set_defaults(func=self._dispatch_generate)

        # --------------------------------------------------------------
        # batch-generate
        # --------------------------------------------------------------
        p_batch_gen = subparsers.add_parser(
            "batch-generate",
            help="Run `generate` on all cases under a directory.",
        )

        p_batch_gen.add_argument(
            "--dry-run",
            action="store_true",
            help="Run each case inside <case>.temp and delete temp on success.",
        )

        p_batch_gen.add_argument(
            "root",
            nargs=1,
            help="Directory containing multiple case folders.",
        )

        p_batch_gen.set_defaults(func=self._dispatch_batch_generate)

        # --------------------------------------------------------------
        # batch-regen
        # --------------------------------------------------------------

        p_batch_regen = subparsers.add_parser(
            "batch-regen",
            help="Run `regen` on all cases under a directory.",
        )

        p_batch_regen.add_argument(
            "--dry-run",
            action="store_true",
            help="Run each case inside <case>.temp and delete temp on success.",
        )

        p_batch_regen.add_argument(
            "root",
            nargs=1,
            help="Directory containing multiple case folders.",
        )

        p_batch_regen.set_defaults(func=self._dispatch_batch_regen)

        # --------------------------------------------------------------
        # batch-quicktest
        # --------------------------------------------------------------

        p_batch_qt = subparsers.add_parser(
            "batch-quicktest",
            help="Run quicktest on all cases under a directory.",
        )

        p_batch_qt.add_argument(
            "--dry-run",
            action="store_true",
            help="Run each case inside <case>.temp and delete temp on success.",
        )

        p_batch_qt.add_argument(
            "root",
            nargs=1,
            help="Directory containing multiple case folders.",
        )

        p_batch_qt.set_defaults(func=self._dispatch_batch_quicktest)

        # --------------------------------------------------------------
        # merge
        # --------------------------------------------------------------

        p_merge = subparsers.add_parser(
            "merge",
            help="Merge multiple integration cases into a new destination case.",
        )

        p_merge.add_argument(
            "--dry-run",
            action="store_true",
            help="Run merge inside <dst>.temp and delete it on success.",
        )

        p_merge.add_argument(
            "--author",
            required=True,
            help="Author for the merged case.",
        )

        p_merge.add_argument(
            "dst",
            help="Destination case directory.",
        )

        p_merge.add_argument(
            "srcs",
            nargs="+",
            help="Source integration cases to merge.",
        )

        p_merge.set_defaults(func=self._dispatch_merge)

        # --------------------------------------------------------------
        # merge-review
        # --------------------------------------------------------------

        p_merge_review = subparsers.add_parser(
            "merge-review",
            help="Preview a merge using dst as the reference case (no filesystem writes).",
        )

        p_merge_review.add_argument(
            "dst",
            help="Destination case directory (reference case).",
        )

        p_merge_review.add_argument(
            "srcs",
            nargs="+",
            help="Source integration cases to merge.",
        )

        p_merge_review.set_defaults(func=self._dispatch_merge_review)

        # --------------------------------------------------------------
        # merge-preview
        # --------------------------------------------------------------

        p_merge_preview = subparsers.add_parser(
            "merge-preview",
            help="Preview a merge by selecting a reference candidate from the source cases.",
        )

        p_merge_preview.add_argument(
            "srcs",
            nargs="+",
            help="Source integration cases to preview merge from.",
        )

        p_merge_preview.add_argument(
            "--compact",
            action="store_true",
            help="Show compact one-line summary output."
        )

        p_merge_preview.add_argument(
            "--json",
            action="store_true",
            help="Output machine-readable JSON."
        )

        p_merge_preview.set_defaults(func=self._dispatch_merge_preview)

        return parser

    # ------------------------------------------------------------------
    # Dispatchers
    # ------------------------------------------------------------------
    def _dispatch_run(self, args) -> int:
        case_path = Path(args.case[0]).resolve()
        return cmd_run.run(case_path, dry_run=args.dry_run)

    def _dispatch_regen(self, args) -> int:
        case_path = Path(args.case[0]).resolve()
        return cmd_regen.regen(case_path, dry_run=args.dry_run)

    def _dispatch_diff(self, case_path: Path) -> int:
        return cmd_diff.diff(case_path)

    def _dispatch_drift(self, case_path: Path) -> int:
        return cmd_drift.drift(case_path)

    def _dispatch_quicktest(self, args) -> int:
        case_path = Path(args.case[0]).resolve()
        return cmd_quicktest.quicktest(case_path, dry_run=args.dry_run)

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

    def _dispatch_new_from_input(self, args) -> int:
        case_path = Path(args.case[0]).resolve()

        inputs_dir = Path(args.inputs[0]).resolve()

        try:
            params = json.loads(args.params)
        except Exception:
            print("[FAIL] --params must be valid JSON")
            return 1

        return cmd_new_from_input.new_from_input(
            case_path,
            inputs_dir,
            builder=args.builder,
            params=params,
            author=args.author,
            accept=args.accept,
            dry_run=args.dry_run,
            force=args.force,
        )

    def _dispatch_generate(self, args) -> int:
        case_path = Path(args.case[0]).resolve()

        if not case_path.exists():
            print(f"[FAIL] Case directory does not exist: {case_path}")
            return 1

        return cmd_generate.generate(
            case_path,
            dry_run=args.dry_run,
        )

    def _dispatch_batch_generate(self, args) -> int:
        root_dir = Path(args.root[0]).resolve()

        return cmd_batch_generate.batch_generate(
            root_dir,
            dry_run=args.dry_run,
        )

    def _dispatch_batch_regen(self, args) -> int:
        root_dir = Path(args.root[0]).resolve()

        return cmd_batch_regen.batch_regen(
            root_dir,
            dry_run=args.dry_run,
        )


    def _dispatch_batch_quicktest(self, args) -> int:
        root_dir = Path(args.root[0]).resolve()

        return cmd_batch_quicktest.batch_quicktest(
            root_dir,
            dry_run=args.dry_run,
        )

    def _dispatch_merge(self, args) -> int:
        dst = Path(args.dst)
        srcs = [Path(p) for p in args.srcs]

        return cmd_merge.merge(
            dst,
            srcs,
            author=args.author,
            dry_run=args.dry_run,
        )

    def _dispatch_merge_review(self, args) -> int:
        dst = Path(args.dst)
        srcs = [Path(p) for p in args.srcs]

        return cmd_merge_review.merge_review(dst, srcs)


    def _dispatch_merge_preview(self, args) -> int:
        srcs = [Path(p) for p in args.srcs]
        return cmd_merge_preview.merge_preview(
            srcs, compact=args.compact, is_json=args.json
        )
