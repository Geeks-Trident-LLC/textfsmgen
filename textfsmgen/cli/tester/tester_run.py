# tester_run.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .tester_manifest_model import Manifest
from .tester_quicktest import _run_builder  # reuse builder hook


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_run(argv: List[str]) -> int:
    """
    textfsmgen tester run <case>

    Loads manifest + inputs, runs builder, compares results to expected_results.
    Returns:
        0 on success (match)
        1 on mismatch or error
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = _resolve_case_dir(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    manifest = _load_manifest(case_dir)
    inputs = _load_inputs(case_dir)

    actual = _run_builder(manifest, inputs)
    expected = _load_expected_results(case_dir)

    if _results_match(expected, actual):
        print(f"[OK] {case} — results match expected")
        return 0

    print(f"[FAIL] {case} — results differ from expected")
    _print_diff(expected, actual)
    return 1


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _resolve_case_dir(case: str) -> Path | None:
    from .tester_paths import resolve_existing_case_path
    return resolve_existing_case_path(case)


def _load_manifest(case_dir: Path) -> Manifest:
    from .tester_manifest_model import load_manifest
    return load_manifest(case_dir)


def _load_inputs(case_dir: Path) -> List[str]:
    """
    Load all input files under inputs/ as raw text.
    """
    inputs_dir = case_dir / "inputs"
    if not inputs_dir.is_dir():
        return []

    texts: List[str] = []
    for file in sorted(inputs_dir.iterdir()):
        if file.is_file():
            texts.append(file.read_text(encoding="utf-8"))
    return texts


def _load_expected_results(case_dir: Path) -> List[Dict[str, Any]]:
    """
    Load expected_results/result.json.
    Returns empty list if missing.
    """
    path = case_dir / "expected_results" / "result.json"
    if not path.is_file():
        return []

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _results_match(expected: List[Dict[str, Any]], actual: List[Dict[str, Any]]) -> bool:
    """
    Strict JSON equality.
    """
    return expected == actual


def _print_diff(expected: Any, actual: Any) -> None:
    """
    Minimal diff printer.
    """
    print("Expected:")
    print(json.dumps(expected, indent=2))
    print("\nActual:")
    print(json.dumps(actual, indent=2))
