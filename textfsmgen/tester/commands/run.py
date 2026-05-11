"""
Implementation of:

    textfsmgen tester run <case>

This action performs a non-destructive test run.

MAIN CASE:
    - Writes meta.json
    - Writes golden.hash

INTEGRATION CASE:
    - Writes nothing

NEVER writes inside:
    canonical/
    expected/
    expected_results/
    inputs/
"""

from __future__ import annotations

from pathlib import Path

from ..core.data_loader import extract_subpath_after
from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase

from .diff import (
    diff_expected,
    diff_against_canonical,
    diff_against_canonical_result,
    diff_against_result,
)


@catch_path_errors
def run(case_path: Path) -> int:
    """
    Execute a non-destructive test run for a single golden test case.

    Returns:
        0 on success
        1 on error
    """

    case = GoldenCase.from_path(case_path)

    if case.is_main():
        return run_canonical(case)
    return run_other(case)


def run_canonical(case) -> int:
    """
    Run the canonical golden test for a case.

    Validates that:
      - The builder can be generated from the canonical sample.
      - The generated snippet and template match the canonical versions.
      - The parsed result matches the canonical expected result.

    Returns:
        0 on success, 1 if any diff or validation failure occurs.
    """

    tc_name = extract_subpath_after("golden", case.case_dir)

    canonical = case.data.load_canonical(root="golden")
    builder = case.data.build(sample=canonical.sample.content)

    if not builder:
        print(f"[FAIL] {tc_name} — failed to generate builder from {canonical.sample.name}")
        return 1

    # Check snippet + template
    for kind in ("snippet", "template"):
        if diff_against_canonical(case, kind=kind):
            print(
                f"[FAIL] {tc_name} — diff found between canonical and generated "
                f"{kind} from {canonical.sample.name}"
            )
            return 1

    # Check parsed result
    if diff_against_canonical_result(case):
        print(
            f"[FAIL] {tc_name} — diff found between canonical result and parsed result "
            f"from {canonical.sample.name}"
        )
        return 1

    case.data.generate_meta()
    case.data.write_golden_hash()

    meta_path = Path(tc_name) / "meta.json"
    hash_path = Path(tc_name) / "golden.hash"

    print(
        f"[OK] {tc_name} — run completed\n"
        f"  Updated: {meta_path}\n"
        f"  Updated: {hash_path}\n"
    )

    return 0


def run_other(case) -> int:
    """
    Run the non‑canonical (expected‑based) golden test for a case.

    Validates that:
      - The generated snippet and template match the expected versions.
      - The parsed result matches the expected result.

    Returns:
        0 on success, 1 if any diff or validation failure occurs.
    """

    tc_name = extract_subpath_after("golden", case.case_dir)

    # Check snippet + template
    for kind in ("snippet", "template"):
        if diff_expected(case, kind=kind):
            print(f"[FAIL] {tc_name} — diff found between expected and generated {kind}")
            return 1

    # Check parsed result
    if diff_against_result(case):
        print(f"[FAIL] {tc_name} — diff found between expected and generated results")
        return 1

    print(f"[OK] {tc_name} — run completed")
    return 0
