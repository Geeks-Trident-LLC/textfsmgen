# tester_regen.py

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from .tester_paths import resolve_case_path, _walk_upwards
from .tester_quicktest import run_quick_test_for_case


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_regen(argv: List[str]) -> int:
    """
    textfsmgen tester regen <case>

    Regenerates all derived artifacts for a single case:
      - expected_results/
      - meta.json
      - golden.hash

    Returns:
        0 on success
        1 on error
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    run_quick_test_for_case(case_dir)
    print(f"[OK] Regenerated: {case}")
    return 0


def handle_tester_regen_all(argv: List[str]) -> int:
    """
    textfsmgen tester regen-all

    Regenerates all golden test cases under tests/golden/*.
    """
    root = _find_golden_root()
    if root is None:
        print("No golden tests found.")
        return 0

    cases = _collect_all_cases(root)
    if not cases:
        print("No cases found under tests/golden.")
        return 0

    for case_dir in cases:
        run_quick_test_for_case(case_dir)
        print(f"[OK] Regenerated: {case_dir.name}")

    return 0


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _find_golden_root() -> Optional[Path]:
    """
    Search upward for tests/golden.
    """
    for root in _walk_upwards(Path.cwd()):
        golden = root / "tests" / "golden"
        if golden.is_dir():
            return golden
    return None


def _collect_all_cases(golden_root: Path) -> List[Path]:
    """
    Collect all valid case directories under tests/golden/*/*.
    Filters out:
      - __pycache__
      - directories starting with '_'
      - directories starting with '.'
    """
    cases: List[Path] = []

    for category_dir in sorted(golden_root.iterdir()):
        if not category_dir.is_dir():
            continue

        # Skip hidden or private categories
        if category_dir.name.startswith("_") or category_dir.name.startswith("."):
            continue
        if category_dir.name == "__pycache__":
            continue

        for case_dir in sorted(category_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            # Skip hidden or private cases
            if case_dir.name.startswith("_") or case_dir.name.startswith("."):
                continue
            if case_dir.name == "__pycache__":
                continue

            cases.append(case_dir)

    return cases

