"""
Implementation of:

    textfsmgen tester regen <case>

Rebuilds *derived artifacts* for a golden test case.

MAIN CASE:
    - expected_results/*.json
    - meta.json
    - golden.hash

INTEGRATION CASE:
    - expected/snippet.txt
    - expected/textfsm.template
    - expected_results/*.json

NEVER writes inside:
    canonical/
    inputs/
    manifest.json
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors
from ..core.data_loader import extract_subpath_after


@catch_path_errors
def regen(case_path: Path, *, dry_run: bool = False) -> int:
    """
    Regen with dry-run support.

    dry-run:
        - Copy <case> → <case>.temp
        - Run regen inside temp
        - Delete temp on success
        - Keep temp on failure
    """

    case_path = case_path.resolve()

    # --------------------------------------------------------------
    # Dry-run: redirect to <case>.temp
    # --------------------------------------------------------------
    if dry_run:
        temp_path = case_path.with_name(case_path.name + ".temp")
        print(f"[DRY-RUN] Using temporary directory: {temp_path}")

        if temp_path.exists():
            shutil.rmtree(temp_path)

        shutil.copytree(case_path, temp_path)
        case_path = temp_path

    # --------------------------------------------------------------
    # Dispatch to main/integration logic
    # --------------------------------------------------------------
    case = GoldenCase.from_path(case_path)

    if case.is_main():
        rc = regen_main(case)
    else:
        rc = regen_integration(case)

    # --------------------------------------------------------------
    # Dry-run cleanup
    # --------------------------------------------------------------
    if dry_run:
        if rc == 0:
            print("[DRY-RUN] Cleaning up temporary directory.")
            shutil.rmtree(case_path)
        else:
            print(
                "[DRY-RUN] Regen failed. Temporary directory preserved for inspection."
            )

    return rc


# ---------------------------------------------------------------------------
# MAIN CASE REGEN
# ---------------------------------------------------------------------------


def regen_main(case: GoldenCase) -> int:
    """
    MAIN CASE:

    Allowed writes:
        - expected_results/*.json
        - meta.json
        - golden.hash

    Forbidden writes:
        - canonical/
        - inputs/
        - manifest.json
    """

    loader = case.data
    canonical = loader.load_canonical()

    updated = []

    # 1. Rebuild expected_results/
    for input_info in loader.load_inputs():
        base = Path(input_info.fullname).stem
        out_path = loader.case_dir / "expected_results" / f"{base}_result.json"

        rows = parse_textfsm_to_dicts(canonical.template.content, input_info.content)
        out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        updated.append(str(out_path))

    # 2. Write meta.json
    loader.write_meta()
    updated.append(str(case.case_dir / "meta.json"))

    # 3. Write golden.hash
    loader.write_golden_hash()
    updated.append(str(case.case_dir / "golden.hash"))

    _print_success(case, updated)
    return 0


# ---------------------------------------------------------------------------
# INTEGRATION CASE REGEN
# ---------------------------------------------------------------------------


def regen_integration(case: GoldenCase) -> int:
    """
    INTEGRATION CASE:

    Allowed writes:
        - expected/snippet.txt
        - expected/textfsm.template
        - expected_results/*.json

    Forbidden writes:
        - canonical/
        - meta.json
        - golden.hash
        - inputs/
        - manifest.json
    """

    loader = case.data
    expected = loader.load_expected()

    snippet_written = False
    updated = []

    for input_info in loader.load_inputs():
        builder = loader.build(input_info.content)
        if not builder:
            print(f"[FAIL] cannot build from input: {input_info.fullname}")
            return 1

        # Write snippet + template only once
        if not snippet_written:
            Path(expected.snippet.fullname).write_text(builder.snippet)
            updated.append(expected.snippet.fullname)

            Path(expected.template.fullname).write_text(builder.template)
            updated.append(expected.template.fullname)

            snippet_written = True

        # Write expected_results/<input>_result.json
        base = Path(input_info.fullname).stem
        out_path = loader.case_dir / "expected_results" / f"{base}_result.json"

        rows = parse_textfsm_to_dicts(builder.template, input_info.content)
        out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        updated.append(str(out_path))

    _print_success(case, updated)
    return 0


# ---------------------------------------------------------------------------
# UTIL
# ---------------------------------------------------------------------------


def _print_success(case: GoldenCase, files: list[str]) -> None:
    tc_name = extract_subpath_after("golden", case.case_dir)
    print(f"[SUCCESS] regenerated {tc_name}")
    for f in files:
        print(f"          - {f}")
