# tester_maintenance.py

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional

from .tester_paths import resolve_existing_case_path, _walk_upwards
from .tester_manifest_model import (
    load_manifest,
    _validate_builder,
    _validate_parameters,
    _validate_meta,
)


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_validate_manifest(argv: List[str]) -> int:
    """
    textfsmgen tester validate-manifest <case>

    Validates:
      - builder
      - parameters (builder-specific)
      - meta (schema_version, required fields)
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    try:
        manifest = load_manifest(case_dir)
        _validate_builder(manifest.builder)
        _validate_parameters(manifest.builder, manifest.parameters)
        _validate_meta(manifest.meta)
    except Exception as e:
        print(f"[FAIL] Manifest invalid: {e}")
        return 1

    print(f"[OK] Manifest valid for case: {case}")
    return 0


def handle_tester_clean(argv: List[str]) -> int:
    """
    textfsmgen tester clean <case>

    Removes derived artifacts:
      - expected_results/
      - meta.json
      - golden.hash
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    _clean_case(case_dir)
    print(f"[OK] Cleaned: {case}")
    return 0


def handle_tester_clean_all(argv: List[str]) -> int:
    """
    textfsmgen tester clean-all

    Removes derived artifacts for all cases under tests/golden/*.
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
        _clean_case(case_dir)
        print(f"[OK] Cleaned: {case_dir.name}")

    return 0


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _clean_case(case_dir: Path) -> None:
    """
    Remove derived artifacts for a single case.
    """
    # expected_results/
    er = case_dir / "expected_results"
    if er.is_dir():
        shutil.rmtree(er)

    # meta.json
    meta = case_dir / "meta.json"
    if meta.is_file():
        meta.unlink()

    # golden.hash
    gh = case_dir / "golden.hash"
    if gh.is_file():
        gh.unlink()


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

