from __future__ import annotations

from pathlib import Path
from .regen import regen as run_regen


def batch_regen(root_dir: Path, *, dry_run: bool) -> int:
    """
    Run `regen` on all cases under a directory.

    Rules:
      - A valid case contains manifest.json and inputs/
      - Each case is processed independently
      - dry-run: each case uses <case>.temp
      - Summary printed at the end
    """

    root_dir = root_dir.resolve()

    if not root_dir.exists() or not root_dir.is_dir():
        print(f"[FAIL] Directory does not exist: {root_dir}")
        return 1

    # --------------------------------------------------------------
    # Discover cases
    # --------------------------------------------------------------
    cases = []
    for p in sorted(root_dir.iterdir()):
        if not p.is_dir():
            continue
        if (p / "manifest.json").exists() and (p / "inputs").exists():
            cases.append(p)

    if not cases:
        print(f"[FAIL] No valid cases found under: {root_dir}")
        return 1

    print(f"[INFO] Found {len(cases)} case(s) to process.")

    # --------------------------------------------------------------
    # Process each case
    # --------------------------------------------------------------
    passed = []
    failed = []

    for case_path in cases:
        print(f"\n[INFO] Processing case: {case_path}")

        rc = run_regen(case_path, dry_run=dry_run)

        if rc == 0:
            passed.append(case_path)
        else:
            failed.append(case_path)

    # --------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------
    print("\n==================== SUMMARY ====================")
    print(f"Total cases: {len(cases)}")
    print(f"Passed     : {len(passed)}")
    print(f"Failed     : {len(failed)}")

    if failed:
        print("\nFailed cases:")
        for c in failed:
            print(f"  - {c}")

    print("=================================================\n")

    return 0 if not failed else 1
