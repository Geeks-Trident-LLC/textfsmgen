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

from pathlib import Path

from ..core.utils import require_case_dir
from .copy import copy_case


def duplicate_case(
    author: str,
    src: Path,
    dry_run: bool = False,
    force: bool = False,
) -> int:

    if "=" in author:
        _, author = author.split("=", maxsplit=1)

    try:
        require_case_dir(src)
    except Exception as exc:
        print(
            "[FAIL]: Duplicate failed because source folder is not a test case folder\n"
            f"  {type(exc).__name__}: {exc}"
        )
        return 1

    parent = src.parent
    base = src.name

    # Generate unique destination unless --force
    if force:
        dst = parent / f"{base}_copy"
    else:
        dst = parent / f"{base}_copy"
        counter = 1
        while dst.exists():
            dst = parent / f"{base}_copy{counter}"
            counter += 1

    return copy_case(
        author=author,
        src=src,
        dst=dst,
        dry_run=dry_run,
        force=force,
    )
