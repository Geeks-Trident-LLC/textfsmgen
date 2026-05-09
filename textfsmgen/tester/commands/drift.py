"""
Implementation of:

    textfsmgen tester drift <case>

This action detects drift between the stored golden.hash and the
freshly computed hash for the case.

IMPORTANT:
- This command is STRICTLY READ-ONLY.
- It NEVER writes meta.json, golden.hash, or any other file.
- It NEVER writes inside:
      canonical/
      expected/
      expected_results/
      inputs/

This module currently provides a placeholder implementation.
The real drift logic will be added later.
"""

from __future__ import annotations

from pathlib import Path

from ..core.utils import require_case_dir


def drift(case_path: Path) -> int:
    """
    Detect drift for a single golden test case.

    Returns:
        0 on success (no drift)
        1 on drift or error
    """
    try:
        require_case_dir(case_path)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Placeholder — real drift logic will be implemented later.
    print(f"[INFO] drift check for case: {case_path.name}")
    print("Drift functionality not implemented yet (read-only placeholder).")

    return 0
