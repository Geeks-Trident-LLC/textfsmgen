# tester_run.py

from __future__ import annotations

import json
import difflib
from pathlib import Path
from typing import Any, Dict, List

from textfsmgen import verify_textfsm

from textfsmgen.libs.common import parse_textfsm_to_dicts

from .tester_manifest_model import load_manifest
from .tester_paths import resolve_existing_case_path
from textfsmgen.core.data_loader import (
    DataLoader,
    is_identical_templates,
    is_identical_snippet
)


def side_by_side_diff(expected_row, actual_row, max_width=40):
    """
    Produce a compact side-by-side diff for a single row (dict vs dict).
    Only mismatched keys are shown.
    """
    keys = sorted(set(expected_row.keys()) | set(actual_row.keys()))
    lines = []
    header = f"{'KEY':20} {'EXPECTED':{max_width}} {'ACTUAL':{max_width}}"
    sep = "-" * (20 + max_width * 2 + 2)
    lines.append(header)
    lines.append(sep)

    def clip(val):
        s = repr(val)
        return s if len(s) <= max_width else s[:max_width - 3] + "..."

    for key in keys:
        exp = expected_row.get(key, "<missing>")
        act = actual_row.get(key, "<missing>")
        if exp != act:
            lines.append(
                f"{key:20} {clip(exp):{max_width}} {clip(act):{max_width}}"
            )

    if len(lines) == 2:
        return "(no differences)"

    return "\n".join(lines)


def diff_dict_lists(expected_list, actual_list):
    """
    Compare two lists of dicts and return a readable side-by-side diff.
    Only mismatched rows are shown.
    """
    diffs = []
    max_len = max(len(expected_list), len(actual_list))

    for i in range(max_len):
        exp = expected_list[i] if i < len(expected_list) else "<missing row>"
        act = actual_list[i] if i < len(actual_list) else "<missing row>"

        if exp != act:
            diffs.append(
                f"Row #{i+1}:\n" +
                side_by_side_diff(exp, act)
            )

    if not diffs:
        return "(no differences)"

    return "\n\n".join(diffs)


def handle_tester_run(argv: List[str]) -> int:
    """
    textfsmgen tester run <case>

    Loads manifest + inputs, instantiates builder exactly like pytest golden tests,
    runs builder, compares results to expected_results.
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    category = case_dir.parent.name
    is_main = (category == "main")
    tc = f"{category}/{case}"

    # Instantiate DataLoader (same as pytest)
    data_info = DataLoader(category, case)
    Builder = data_info.get_builder()

    # -------------------------
    # MAIN CASE
    # -------------------------
    if is_main:
        canonical_sample = data_info.canonical_sample
        canonical_snippet = data_info.canonical_snippet
        canonical_template = data_info.canonical_template
        canonical_result = data_info.canonical_result
        params = data_info.parameters

        builder = Builder(user_data=canonical_sample, **params)

        if not bool(builder):
            print(f"[FAIL] {tc} — cannot use canonical sample to build TextFSM template.")
            return 1

        if not is_identical_snippet(builder.snippet, canonical_snippet):
            print(f"[FAIL] {tc} - generated snippet differs from canonical snippet")
            print(f"Canonical snippet:\n====================\n{canonical_snippet}")
            print("-" * 60)
            print(f"Generated snippet:\n====================\n{builder.snippet}")
            return 1

        if not is_identical_templates(builder.template, canonical_template):
            print(f"[FAIL] {tc} - generated template differs from canonical template")
            print(f"Canonical template:\n====================\n{canonical_template}")
            print("-" * 60)
            print(f"Generated template:\n====================\n{builder.template}")
            return 1

        status = verify_textfsm(
            canonical_template,
            canonical_sample,
            expected_result=canonical_result
        )
        if not status:
            print(f"[FAIL] {tc} - generated result differs from canonical result")
            print(status)
            return 1

        groups = []
        checks = []
        count = 1

        # Parse each input sample
        for input_sample_info, exp_result_info in data_info.get_input_and_expected_result():
            input_sample = input_sample_info["data"]
            exp_result = exp_result_info["data"]

            result = parse_textfsm_to_dicts(canonical_template, input_sample)
            checks.append(result == exp_result)

            if result != exp_result:
                diff_output = diff_dict_lists(exp_result, result)
                groups.append(
                    f"\n--- Sample #{count} --- "
                    f"(rows: actual={len(result)}, expected={len(exp_result)})\n"
                    f"{diff_output}\n"
                )

            count += 1

        if all(checks):
            print(f"[OK] {tc} — results match expected")
            return 0

        print(f"[FAIL] {tc} - results differ from expected")
        print("".join(groups))
        return 1

    # -------------------------
    # INTEGRATION CASE
    # -------------------------
    else:
        exp_snippet = data_info.expected_snippet
        exp_template = data_info.expected_template
        params = data_info.parameters

        first_input_info, _ = next(data_info.get_input_and_expected_result())
        first_input = first_input_info["data"]

        builder = Builder(user_data=first_input, **params)

        if not bool(builder):
            print(f"[FAIL] {tc} — cannot use user input to build TextFSM template.")
            return 1

        if not is_identical_snippet(builder.snippet, exp_snippet):
            print(f"[FAIL] {tc} - generated snippet differs from expected snippet")
            print(f"Expected snippet:\n====================\n{exp_snippet}")
            print("-" * 60)
            print(f"Generated snippet:\n====================\n{builder.snippet}")
            return 1

        if not is_identical_templates(builder.template, exp_template):
            print(f"[FAIL] {tc} - generated template differs from expected template")
            print(f"Expected template:\n====================\n{exp_template}")
            print("-" * 60)
            print(f"Generated template:\n====================\n{builder.template}")
            return 1

        groups = []
        checks = []
        count = 1

        # Parse each input sample
        for input_sample_info, exp_result_info in data_info.get_input_and_expected_result():
            input_sample = input_sample_info["data"]
            exp_result = exp_result_info["data"]

            result = parse_textfsm_to_dicts(exp_template, input_sample)
            checks.append(result == exp_result)

            if result != exp_result:
                diff_output = diff_dict_lists(exp_result, result)
                groups.append(
                    f"\n--- Sample #{count} --- "
                    f"(rows: actual={len(result)}, expected={len(exp_result)})\n"
                    f"{diff_output}\n"
                )

            count += 1

        if all(checks):
            print(f"[OK] {tc} — results match expected")
            return 0

        print(f"[FAIL] {tc} - results differ from expected")
        print("".join(groups))
        return 1

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

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
    """
    Load expected_results/*.json (multiple files).
    """
    expected_dir = case_dir / "expected_results"
    if not expected_dir.is_dir():
        return []

    results = []
    for file in sorted(expected_dir.iterdir()):
        if file.suffix == ".json":
            results.append(json.loads(file.read_text(encoding="utf-8")))
    return results


def _print_diff(expected: Any, actual: Any) -> None:
    print("Expected:")
    print(json.dumps(expected, indent=2))
    print("\nActual:")
    print(json.dumps(actual, indent=2))
