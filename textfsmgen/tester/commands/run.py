"""
Implementation of:

    textfsmgen tester run <case>

This action performs a non-destructive test run.

MAIN CASE:
    - Writes meta.json
    - Writes golden.hash

INTEGRATION CASE:
    - Writes nothing

NEVER writes inside:
    canonical/
    expected/
    expected_results/
    inputs/
"""

from __future__ import annotations

from pathlib import Path
import shutil

from .shared import run_canonical, run_expected
from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase


@catch_path_errors
def run(case_path: Path, *, dry_run: bool = False) -> int:
    """
    Execute a non-destructive test run for a single golden test case.

    dry-run:
        - Copy <case> → <case>.temp
        - Run inside temp
        - Delete temp on success
        - Keep temp on failure

    Returns:
        0 on success
        1 on error
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
    # Dispatch to canonical or expected run
    # --------------------------------------------------------------
    case = GoldenCase.from_path(case_path)

    if case.is_main():
        rc = run_canonical(case, is_quicktest=False)
    else:
        rc = run_expected(case, is_quicktest=False)

    # --------------------------------------------------------------
    # Dry-run cleanup
    # --------------------------------------------------------------
    if dry_run:
        if rc == 0:
            print("[DRY-RUN] Cleaning up temporary directory.")
            shutil.rmtree(case_path)
        else:
            print("[DRY-RUN] Run failed. Temporary directory preserved for inspection.")

    return rc
