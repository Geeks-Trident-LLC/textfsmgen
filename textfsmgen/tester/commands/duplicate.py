"""
Implementation of:

    textfsmgen tester duplicate author=<author> <target-case>

This action duplicates a golden test case by creating a new case
with an auto-generated name:

    <target-case>-duplicated
    <target-case>-duplicated-2
    <target-case>-duplicated-3
    ...

Rules:
- EXACTLY ONE target-case is allowed (enforced by CLI).
- Must provide: author=<name>
- NEVER writes inside the source case's:
      canonical/
      expected/
      expected_results/
      inputs/
- Delegates actual copying to the copy_case() logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ..core.utils import require_case_dir
from .copy import copy_case


def duplicate(case_path: Path) -> int:
    """
    Entry point for:

        textfsmgen tester duplicate author=<author> <target-case>

    The unified CLI passes only <target-case> here.
    We must parse author=<name> and generate <new-case>.
    """
    argv = sys.argv
    # argv example:
    #   ['textfsmgen', 'tester', 'duplicate', 'author=Bob', 'oldcase']

    # ------------------------------------------------------------------
    # Parse author=<name>
    # ------------------------------------------------------------------
    author = ""
    extra_args = []

    for arg in argv[3:]:  # skip: textfsmgen tester duplicate
        if arg.startswith("author="):
            author = arg.split("=", 1)[1].strip()
        else:
            extra_args.append(arg)

    if not author:
        print("ERROR: Missing required argument: author=<name>")
        return 1

    # ------------------------------------------------------------------
    # Parse <target-case>
    # ------------------------------------------------------------------
    if len(extra_args) != 1:
        print("ERROR: duplicate requires: author=<name> <target-case>")
        return 1

    target_case = Path(extra_args[0]).resolve()

    # ------------------------------------------------------------------
    # Validate target case
    # ------------------------------------------------------------------
    try:
        require_case_dir(target_case)
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # ------------------------------------------------------------------
    # Generate new-case name with suffixes
    # ------------------------------------------------------------------
    base_name = target_case.name + "-duplicated"
    parent = target_case.parent

    new_case = parent / base_name
    counter = 2

    while new_case.exists():
        new_case = parent / f"{base_name}-{counter}"
        counter += 1

    # ------------------------------------------------------------------
    # Inject new-case into argv so copy_case() can reuse its logic
    # ------------------------------------------------------------------
    # We rewrite argv to:
    #   textfsmgen tester copy author=<author> <target-case> <new-case>
    sys.argv = [
        argv[0],
        argv[1],
        "copy",
        f"author={author}",
        str(target_case),
        str(new_case),
    ]

    # ------------------------------------------------------------------
    # Delegate to copy_case()
    # ------------------------------------------------------------------
    return copy_case(target_case)
