# tester_info.py

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .tester_paths import resolve_existing_case_path


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_list(argv: List[str]) -> int:
    """
    textfsmgen tester list

    Lists all cases under tests/golden/*.
    """
    # -------------------------------------------------------------------------
    def _is_valid_case_name(name: str) -> bool:
        if name == "__pycache__":
            return False
        if name.startswith("_"):
            return False
        if name.startswith("."):
            return False
        return True
    # -------------------------------------------------------------------------

    golden_root = _find_golden_root()
    if golden_root is None:
        print("No golden tests found.")
        return 0

    for category_dir in sorted(golden_root.iterdir()):
        if not category_dir.is_dir():
            continue
        if not _is_valid_case_name(category_dir.name):
            continue

        print(f"[{category_dir.name}]")

        for case_dir in sorted(category_dir.iterdir()):
            if not case_dir.is_dir():
                continue
            if not _is_valid_case_name(case_dir.name):
                continue

            print(f"  - {case_dir.name}")

    return 0


def handle_tester_info(argv: List[str]) -> int:
    """
    textfsmgen tester info <case>

    Shows manifest + basic metadata for a case.
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    manifest = _load_manifest(case_dir)
    meta_path = case_dir / "meta.json"

    print(f"Case: {case}")
    print(f"Category: {manifest.category}")
    print(f"Builder: {manifest.builder}")
    print("Parameters:")
    _print_dict(manifest.parameters, indent=2)

    print("Meta:")
    _print_dict(manifest.meta.__dict__, indent=2)

    if meta_path.is_file():
        print("Derived meta.json:")
        derived = json.loads(meta_path.read_text(encoding="utf-8"))
        _print_dict(derived, indent=2)

    return 0


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _find_golden_root() -> Optional[Path]:
    """
    Search upward for tests/golden.
    """
    from .tester_paths import _walk_upwards

    for root in _walk_upwards(Path.cwd()):
        golden = root / "tests" / "golden"
        if golden.is_dir():
            return golden
    return None


def _load_manifest(case_dir: Path):
    from .tester_manifest_model import load_manifest
    return load_manifest(case_dir)


def _print_dict(data: Dict[str, Any], indent: int = 0) -> None:
    """
    Pretty-print a dict with indentation.
    """
    pad = " " * indent
    for key, value in data.items():
        print(f"{pad}{key}: {value}")
