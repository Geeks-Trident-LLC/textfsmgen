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

from .shared import run_canonical, run_expected
from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase


@catch_path_errors
def run(case_path: Path) -> int:
    """
    Execute a non-destructive test run for a single golden test case.

    Returns:
        0 on success
        1 on error
    """

    case = GoldenCase.from_path(case_path)

    if case.is_main():
        return run_canonical(case, is_quicktest=False)
    return run_expected(case, is_quicktest=False)
