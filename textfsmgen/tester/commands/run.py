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

from ..core.utils import require_case_dir
from ..core.golden_case import GoldenCase


def run(case_path: Path) -> int:
    """
    Execute a non-destructive test run for a single golden test case.

    Returns:
        0 on success
        1 on error
    """
    try:
        require_case_dir(case_path)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    case = GoldenCase.from_path(case_path)

    try:
        case.run()
    except Exception as e:
        print(f"[FAIL] {case_path.name} — run failed: {e}")
        return 1

    print(f"[OK] {case_path.name} — run completed")
    return 0
