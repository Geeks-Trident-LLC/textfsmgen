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

from .shared import run_canonical, run_expected, print_status
from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase

from textfsmgen.libs import file


@catch_path_errors
def run(
    case_path: Path,
    *,
    sandbox: bool = False,
    sandbox_keep: bool = False,
    quicktest: bool = False,
) -> int:
    case_path = case_path.resolve()

    # --------------------------------------------------------------
    # Quicktest: fast, no writes, no temp dirs
    # --------------------------------------------------------------
    if quicktest:
        case = GoldenCase.from_path(case_path)
        return (
            run_canonical(case, quicktest=True)
            if case.is_main()
            else run_expected(case, quicktest=True)
        )

    # --------------------------------------------------------------
    # Sandbox modes: create <case>.temp and run inside it
    # --------------------------------------------------------------
    if sandbox or sandbox_keep:
        temp_path = case_path.with_name(case_path.name + ".temp")
        print_status(
            f"Using temporary directory: {file.path_name(temp_path)}",
            sandbox=True,
        )

        if temp_path.exists():
            shutil.rmtree(temp_path)

        shutil.copytree(case_path, temp_path)
        case_path = temp_path

        case = GoldenCase.from_path(case_path)
        rc = (
            run_canonical(case, quicktest=False)
            if case.is_main()
            else run_expected(case, quicktest=False)
        )

        if sandbox:
            if rc == 0:
                print_status("Cleaning up temporary directory.", sandbox=True)
                shutil.rmtree(case_path)
            else:
                print_status("Run failed. Temporary directory preserved.", sandbox=True)
        else:
            print_status("Preserving temporary directory.", sandbox=True)

        return rc

    # --------------------------------------------------------------
    # Normal run (in-place)
    # --------------------------------------------------------------
    case = GoldenCase.from_path(case_path)
    return (
        run_canonical(case, quicktest=False)
        if case.is_main()
        else run_expected(case, quicktest=False)
    )
