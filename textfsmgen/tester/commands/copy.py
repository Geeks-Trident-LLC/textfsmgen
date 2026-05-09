"""
Implementation of:

    textfsmgen tester copy author=<author> <target-case> <new-case>

This action creates a NEW golden test case by copying an existing one.

Rules:
- EXACTLY ONE target-case is allowed (enforced by CLI).
- Must provide: author=<name>
- Must provide: <new-case> directory path
- Copies ONLY authoritative files:
      canonical/  (if main)
      expected/   (if integration)
      inputs/
- NEVER copies:
      expected_results/
      meta.json
      golden.hash
- After copying, generates:
      meta.json
      golden.hash

NEVER writes inside the source case's:
      canonical/
      expected/
      expected_results/
      inputs/
"""

from __future__ import annotations

import shutil
from pathlib import Path

from ..core.utils import require_case_dir, is_protected_dir
from ..core.golden_case import GoldenCase
from ..core.data_loader import DataLoader


def copy_case(case_path: Path) -> int:
    """
    Entry point for:

        textfsmgen tester copy author=<author> <target-case> <new-case>

    The unified CLI passes only <target-case> here.
    We must parse the remaining arguments manually.
    """
    import sys

    argv = sys.argv
    # argv example:
    #   ['textfsmgen', 'tester', 'copy', 'author=Bob', 'oldcase', 'newcase']

    # ------------------------------------------------------------------
    # Parse author=<name>
    # ------------------------------------------------------------------
    author = ""
    extra_args = []

    for arg in argv[3:]:  # skip: textfsmgen tester copy
        if arg.startswith("author="):
            author = arg.split("=", 1)[1].strip()
        else:
            extra_args.append(arg)

    if not author:
        print("ERROR: Missing required argument: author=<name>")
        return 1

    # ------------------------------------------------------------------
    # Parse <target-case> and <new-case>
    # ------------------------------------------------------------------
    if len(extra_args) != 2:
        print("ERROR: copy requires: author=<name> <target-case> <new-case>")
        return 1

    target_case = Path(extra_args[0]).resolve()
    new_case = Path(extra_args[1]).resolve()

    # ------------------------------------------------------------------
    # Validate target case
    # ------------------------------------------------------------------
    try:
        require_case_dir(target_case)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # ------------------------------------------------------------------
    # Validate new case does not exist
    # ------------------------------------------------------------------
    if new_case.exists():
        print(f"ERROR: New case already exists: {new_case}")
        return 1

    # ------------------------------------------------------------------
    # Load target case
    # ------------------------------------------------------------------
    source = GoldenCase.from_path(target_case)
    source_loader = DataLoader(target_case)

    # ------------------------------------------------------------------
    # Create new case directory
    # ------------------------------------------------------------------
    new_case.mkdir(parents=True, exist_ok=False)

    # ------------------------------------------------------------------
    # Copy authoritative directories
    # ------------------------------------------------------------------
    try:
        if source.is_main():
            _copy_dir_if_exists(target_case / "canonical", new_case / "canonical")
        else:
            _copy_dir_if_exists(target_case / "expected", new_case / "expected")

        _copy_dir_if_exists(target_case / "inputs", new_case / "inputs")

    except Exception as e:
        print(f"ERROR: Failed copying authoritative files: {e}")
        return 1

    # ------------------------------------------------------------------
    # NEVER copy derived files
    # ------------------------------------------------------------------
    # expected_results/
    # meta.json
    # golden.hash
    # (We simply do nothing here.)

    # ------------------------------------------------------------------
    # Write new meta.json + golden.hash
    # ------------------------------------------------------------------
    try:
        new_loader = DataLoader(new_case)
        new_loader.write_meta(approved_by=author)
        new_loader.write_golden_hash()
    except Exception as e:
        print(f"ERROR: Failed generating metadata: {e}")
        return 1

    print(f"[OK] Copied case '{target_case.name}' → '{new_case.name}'")
    return 0


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _copy_dir_if_exists(src: Path, dst: Path) -> None:
    """
    Copy a directory if it exists.

    NEVER copy protected directories from the source case.
    """
    if not src.exists():
        return

    if is_protected_dir(src):
        # Should never happen because caller controls which dirs are copied.
        raise RuntimeError(f"Attempted to copy protected directory: {src}")

    shutil.copytree(src, dst)
