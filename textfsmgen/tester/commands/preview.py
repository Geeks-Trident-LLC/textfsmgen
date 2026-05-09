"""
Implementation of:

    textfsmgen tester preview <case>

This action previews parsing results or generated artifacts for a case.

IMPORTANT:
- This command is STRICTLY READ-ONLY.
- It NEVER writes meta.json, golden.hash, or any other file.
- It NEVER writes inside:
      canonical/
      expected/
      expected_results/
      inputs/

This module currently provides a placeholder implementation.
The real preview logic will be added later.
"""

from __future__ import annotations

from pathlib import Path

from ..core.utils import require_case_dir


def preview(case_path: Path) -> int:
    """
    Preview parsing results for a single golden test case.

    Returns:
        0 on success
        1 on error
    """
    try:
        require_case_dir(case_path)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Placeholder — real preview logic will be implemented later.
    print(f"[INFO] preview for case: {case_path.name}")
    print("Preview functionality not implemented yet (read-only placeholder).")

    return 0
