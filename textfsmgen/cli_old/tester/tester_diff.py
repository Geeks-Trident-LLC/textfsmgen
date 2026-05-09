# tester_diff.py

from __future__ import annotations

import json
import difflib
from pathlib import Path
from typing import List, Optional, Any, Dict

from .tester_paths import resolve_case_path
from .tester_manifest_model import Manifest
from .tester_quicktest import _run_builder


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_diff(argv: List[str]) -> int:
    """
    Handles:
      textfsmgen tester diff-template <case>
      textfsmgen tester diff-snippet <case>
      textfsmgen tester diff-results <case>

    The dispatcher in cli_tester.py routes all diff-* commands here.
    """
    if len(argv) < 2:
        print("error: usage: tester diff-<type> <case>")
        return 1

    diff_type = argv[0]
    case = argv[1]

    case_dir = resolve_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    if diff_type == "diff-template":
        return _diff_template(case_dir)

    if diff_type == "diff-snippet":
        return _diff_snippet(case_dir)

    if diff_type == "diff-results":
        return _diff_results(case_dir)

    print(f"error: unknown diff type: {diff_type}")
    return 1


# ------------------------------------------------------------
# Diff handlers
# ------------------------------------------------------------

def _diff_template(case_dir: Path) -> int:
    """
    Compare authoritative template vs generated template.
    """
    auth = _load_authoritative_file(case_dir, "textfsm.template")
    if auth is None:
        print("error: authoritative template not found")
        return 1

    generated = _generate_template(case_dir)
    if generated is None:
        print("error: builder did not produce generated_template")
        return 1

    return _print_text_diff(auth, generated)


def _diff_snippet(case_dir: Path) -> int:
    """
    Compare authoritative snippet vs generated snippet.
    """
    auth = _load_authoritative_file(case_dir, "snippet.txt")
    if auth is None:
        print("error: authoritative snippet not found")
        return 1

    generated = _generate_snippet(case_dir)
    if generated is None:
        print("error: builder did not produce generated_snippet")
        return 1

    return _print_text_diff(auth, generated)


def _diff_results(case_dir: Path) -> int:
    """
    Compare expected_results/result.json vs builder output.
    """
    expected = _load_expected_results(case_dir)
    actual = _generate_results(case_dir)

    expected_str = json.dumps(expected, indent=2)
    actual_str = json.dumps(actual, indent=2)

    return _print_text_diff(expected_str, actual_str)


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _load_authoritative_file(case_dir: Path, filename: str) -> Optional[str]:
    """
    Load authoritative file depending on category:
      - main → canonical/<filename>
      - non-main → expected/<filename>
    """
    category = case_dir.parent.name

    if category == "main":
        path = case_dir / "canonical" / filename
    else:
        path = case_dir / "expected" / filename

    if not path.is_file():
        return None

    return path.read_text(encoding="utf-8")


def _generate_template(case_dir: Path) -> Optional[str]:
    """
    Run builder and extract generated_template.
    """
    manifest = _load_manifest(case_dir)
    inputs = _load_inputs(case_dir)
    result = _run_builder(manifest, inputs)

    if not result or not isinstance(result, list):
        return None

    first = result[0]
    return first.get("generated_template")


def _generate_snippet(case_dir: Path) -> Optional[str]:
    """
    Run builder and extract generated_snippet.
    """
    manifest = _load_manifest(case_dir)
    inputs = _load_inputs(case_dir)
    result = _run_builder(manifest, inputs)

    if not result or not isinstance(result, list):
        return None

    first = result[0]
    return first.get("generated_snippet")


def _generate_results(case_dir: Path) -> List[Dict[str, Any]]:
    """
    Run builder and return parsed rows.
    """
    manifest = _load_manifest(case_dir)
    inputs = _load_inputs(case_dir)
    result = _run_builder(manifest, inputs)

    if not result or not isinstance(result, list):
        return []

    return result


def _load_manifest(case_dir: Path) -> Manifest:
    from .tester_manifest_model import load_manifest
    return load_manifest(case_dir)


def _load_inputs(case_dir: Path) -> List[str]:
    inputs_dir = case_dir / "inputs"
    if not inputs_dir.is_dir():
        return []

    texts: List[str] = []
    for file in sorted(inputs_dir.iterdir()):
        if file.is_file():
            texts.append(file.read_text(encoding="utf-8"))
    return texts


def _load_expected_results(case_dir: Path) -> List[Dict[str, Any]]:
    path = case_dir / "expected_results" / "result.json"
    if not path.is_file():
        return []

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _print_text_diff(a: str, b: str) -> int:
    """
    Print unified diff between two strings.
    Returns:
        0 if identical
        1 if different
    """
    if a == b:
        print("[OK] No differences")
        return 0

    diff = difflib.unified_diff(
        a.splitlines(),
        b.splitlines(),
        fromfile="expected",
        tofile="actual",
        lineterm="",
    )

    print("\n".join(diff))
    return 1
