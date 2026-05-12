"""
Implementation of:

    textfsmgen tester quicktest <case>

This action performs a fast, read-only test run without writing any files.

IMPORTANT:
- This command is STRICTLY READ-ONLY.
- It NEVER writes meta.json, golden.hash, or any other file.
- It NEVER writes inside:
      canonical/
      expected/
      expected_results/
      inputs/

This module currently provides a placeholder implementation.
The real quicktest logic will be added later.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase

from .shared import run_canonical, run_expected



@catch_path_errors
def quicktest(case_path: Path, *, dry_run: bool = False) -> int:
    """
    Run quicktest for a single golden test case.

    dry-run:
        - Copy <case> → <case>.temp
        - Run quicktest inside temp
        - Delete temp on success
        - Keep temp on failure
    """

    case_path = case_path.resolve()

    # --------------------------------------------------------------
    # Dry-run: redirect to <case>.temp
    # --------------------------------------------------------------
    if dry_run:
        temp_path = case_path.with_name(case_path.name + ".temp")
        print(f"[DRY-RUN] Using temporary directory: {temp_path}")

        if temp_path.exists():
            shutil.rmtree(temp_path)

        shutil.copytree(case_path, temp_path)
        case_path = temp_path

    # --------------------------------------------------------------
    # Dispatch to canonical or expected quicktest
    # --------------------------------------------------------------
    case = GoldenCase.from_path(case_path)

    if case.is_main():
        rc = run_canonical(case, is_quicktest=True)
    else:
        rc = run_expected(case, is_quicktest=True)

    # --------------------------------------------------------------
    # Dry-run cleanup
    # --------------------------------------------------------------
    if dry_run:
        if rc == 0:
            print("[DRY-RUN] Cleaning up temporary directory.")
            shutil.rmtree(case_path)
        else:
            print("[DRY-RUN] Quicktest failed. Temporary directory preserved for inspection.")

    return rc

