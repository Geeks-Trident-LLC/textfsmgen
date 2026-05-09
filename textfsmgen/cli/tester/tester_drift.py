# tester_drift.py

from __future__ import annotations

import os
import hashlib
from pathlib import Path
from typing import List

from .tester_paths import resolve_case_path


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_drift(argv: List[str]) -> int:
    """
    textfsmgen tester drift <case>

    Compares the current golden.hash with a freshly computed hash.
    Returns:
        0 if no drift
        1 if drift detected or error
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    stored = _load_stored_hash(case_dir)
    if stored is None:
        print(f"[FAIL] {case} — golden.hash missing. Run: pytest --regen-golden")
        return 1

    current = _compute_current_hash(case_dir)

    if stored == current:
        print(f"[OK] {case} — no drift detected")
        return 0

    print(f"[FAIL] {case} — drift detected")
    _print_drift_details(case_dir, stored, current)
    return 1


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _load_stored_hash(case_dir: Path) -> str | None:
    """
    Load golden.hash if present.
    """
    path = case_dir / "golden.hash"
    if not path.is_file():
        return None

    return path.read_text(encoding="utf-8").strip()


def _compute_current_hash(case_dir: Path) -> str:
    """
    Compute SHA256 hash of all authoritative + derived files,
    excluding golden.hash itself.
    """
    files = _collect_files_for_hash(case_dir)
    return _compute_hash(files)


def _collect_files_for_hash(case_dir: Path) -> List[Path]:
    """
    Collect all files that should be included in golden.hash.
    Excludes:
      - golden.hash
    """
    collected: List[Path] = []

    for root, _, files in os.walk(case_dir):
        for name in files:
            path = Path(root) / name
            if path.name == "golden.hash":
                continue
            collected.append(path)

    return sorted(collected)


def _compute_hash(files: List[Path]) -> str:
    """
    Compute SHA256 hash of all file contents in sorted order.
    """
    h = hashlib.sha256()

    for file in files:
        data = file.read_bytes()
        h.update(data)

    return h.hexdigest()


def _print_drift_details(case_dir: Path, stored: str, current: str) -> None:
    """
    Print minimal drift information.
    """
    print(f"Stored hash:  {stored}")
    print(f"Current hash: {current}")
    print("Files included in hash:")

    for path in _collect_files_for_hash(case_dir):
        print(f"  - {path.relative_to(case_dir)}")
