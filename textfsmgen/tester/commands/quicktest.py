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

from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase

from .shared import run_canonical, run_expected


@catch_path_errors
def quicktest(case_path: Path) -> int:
    """
    Perform a fast, read-only test run for a single golden test case.

    Returns:
        0 on success
        1 on error
    """
    case = GoldenCase.from_path(case_path)

    if case.is_main():
        return run_canonical(case, is_quicktest=True)
    return run_expected(case, is_quicktest=True)
