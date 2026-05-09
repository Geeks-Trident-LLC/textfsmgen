"""
Implementation of:

    textfsmgen tester diff <case>

This action shows differences between expected and actual results.

IMPORTANT:
- This command is STRICTLY READ-ONLY.
- It NEVER writes meta.json, golden.hash, or any other file.
- It NEVER writes inside:
      canonical/
      expected/
      expected_results/
      inputs/

This module currently provides a placeholder implementation.
The real diff logic will be added later.
"""

from __future__ import annotations

from pathlib import Path

from ..core.utils import require_case_dir


def diff(case_path: Path) -> int:
    """
    Display differences for a single golden test case.

    Returns:
        0 on success
        1 on error
    """
    try:
        require_case_dir(case_path)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Placeholder — real diff logic will be implemented later.
    print(f"[INFO] diff for case: {case_path.name}")
    print("Diff functionality not implemented yet (read-only placeholder).")

    return 0
