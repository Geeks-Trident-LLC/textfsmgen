from __future__ import annotations

from pathlib import Path
import json
import difflib

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.data_loader import extract_subpath_after
from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors

# Reuse merge-preview helpers
from .merge_preview import (
    merge_preview_load_and_validate_cases,
    merge_preview_validate_builder_type,
    merge_preview_select_reference_case,
    merge_preview_simulate_input_merge,
)


@catch_path_errors
def merge_diff(
    srcs: list[Path],
    *,
    compact: bool = False,
    is_json: bool = False,
    diff_count: int = 2,
    diff_names_only: bool = False,
) -> int:

    display = not (compact or is_json)

    if display:
        print("[MERGE-DIFF] Starting diff...\n")

    # 1. Load and validate cases
    cases = merge_preview_load_and_validate_cases(srcs, display=display)
    if cases is None:
        return 1

    # 2. Validate builder type
    builder_type = merge_preview_validate_builder_type(cases, display=display)
    if builder_type is None:
        return 1

    # 3. Evaluate reference candidates (internal only)
    ref_case, candidate_info = merge_preview_select_reference_case(cases, display=False)
    if ref_case is None:
        if is_json:
            print(merge_diff_json_fail(candidate_info))
        else:
            print("[MERGE-DIFF] No valid reference case found. Merge would fail.")
        return 1

    ref_case_name = extract_subpath_after("golden", ref_case.case_dir)

    if display:
        print(f"[MERGE-DIFF] Reference case: {ref_case_name}")

    # 4. Simulate input merge
    merge_actions, simulated_inputs = merge_preview_simulate_input_merge(
        cases, ref_case
    )

    if display:
        print(f"[MERGE-DIFF] Total merged inputs: {len(simulated_inputs)}\n")

    # 5. Generate merged expected_results
    merged_results = merge_diff_generate_results(ref_case, simulated_inputs)

    # 6. Compare merged vs golden expected_results
    diffs = merge_diff_compare_results(ref_case, merged_results)

    # 7. Output modes
    # JSON mode
    if is_json:
        print(merge_diff_json_success(ref_case_name, diffs, len(simulated_inputs)))
        return 0 if all(v == "match" for v in diffs.values()) else 1

    # Compact mode
    if compact:
        merge_diff_print_compact(ref_case_name, diffs, len(simulated_inputs))
        return 0 if all(v == "match" for v in diffs.values()) else 1

    # Names-only mode
    if diff_names_only:
        diff_list = [name for name, status in diffs.items() if status != "match"]

        print("[MERGE-DIFF] Files with differences:")
        if not diff_list:
            print("  (none)")
            print("\n[MERGE-DIFF] All results match.")
            return 0

        for name in diff_list:
            print(f"  expected_results/{name}_result.json")

        print("\n[MERGE-DIFF] Differences detected.")
        return 1

    # Normal mode
    merge_diff_print_normal(ref_case, diffs, merged_results, diff_count)
    all_match = all(v == "match" for v in diffs.values())

    if all_match:
        print("\n[MERGE-DIFF] All results match.")
        return 0

    print("\n[MERGE-DIFF] Differences detected.")
    return 1


# ---------------------------------------------------------------------------
# Generate merged expected_results
# ---------------------------------------------------------------------------


def merge_diff_generate_results(ref_case: GoldenCase, simulated_inputs: dict[str, str]):
    template = ref_case.data.load_expected().template.content
    merged = {}

    for name, content in simulated_inputs.items():
        rows = parse_textfsm_to_dicts(template, content)
        merged[name] = rows

    return merged


# ---------------------------------------------------------------------------
# Compare merged vs golden expected_results
# ---------------------------------------------------------------------------


def merge_diff_compare_results(
    ref_case: GoldenCase, merged_results: dict[str, list[dict]]
):
    diffs = {}
    for name, merged_rows in merged_results.items():
        base = Path(name).stem
        base_dir_path = Path(name).parent.parent
        expected_path = base_dir_path / "expected_results" / f"{base}_result.json"
        if not expected_path.exists():
            diffs[name] = "missing"
            continue

        expected_rows = json.loads(expected_path.read_text())

        if expected_rows == merged_rows:
            diffs[name] = "match"
        else:
            diffs[name] = "diff"

    return diffs


# ---------------------------------------------------------------------------
# Normal mode printing
# ---------------------------------------------------------------------------


def merge_diff_print_normal(ref_case, diffs, merged_results, diff_count):
    for name, status in diffs.items():
        # name is now a full path, so extract just the filename
        file_path = Path(name)
        base = file_path.stem  # e.g. "list_files.txt"
        result_path = extract_subpath_after(
            "golden",
            file_path.parent.parent / "expected_results" / f"{base}_result.json",
        )

        # Print the diff header
        print(f"[DIFF] {result_path}")

        if status == "match":
            print("  ✓ No differences\n")
            continue

        # Golden expected result file
        expected_path = ref_case.case_dir / "expected_results" / f"{base}_result.json"
        expected_text = expected_path.read_text() if expected_path.exists() else ""

        # Generated merged result
        merged_text = json.dumps(merged_results[name], indent=2)

        # Unified diff lines
        diff_lines = list(
            difflib.unified_diff(
                expected_text.splitlines(),
                merged_text.splitlines(),
                fromfile="expected",
                tofile="merged",
                lineterm="",
            )
        )

        printed = 0
        for line in diff_lines:
            print(line)
            if line.startswith("@@"):
                printed += 1
                if printed >= diff_count:
                    print("  ... (diff truncated)\n")
                    break

        print()


# ---------------------------------------------------------------------------
# Compact mode
# ---------------------------------------------------------------------------


def merge_diff_print_compact(ref_case_name, diffs, total_inputs):
    diff_count = sum(1 for v in diffs.values() if v != "match")

    print(f"[MERGE-DIFF] Reference: {ref_case_name}")
    print(f"[MERGE-DIFF] Inputs: {total_inputs}, diffs: {diff_count}")
    print(f"[MERGE-DIFF] Result: {'success' if diff_count == 0 else 'fail'}")


# ---------------------------------------------------------------------------
# JSON mode
# ---------------------------------------------------------------------------


def merge_diff_json_success(ref_case_name, diffs, total_inputs):
    clean_diffs = {}
    for file_name, value in diffs.items():
        file_path = Path(file_name)
        key = (
            str(extract_subpath_after("golden", file_path))
            if file_path.is_absolute()
            else str(file_path)
        )
        clean_diffs[key] = value

    data = {
        "reference_case": str(ref_case_name),
        "inputs_total": total_inputs,
        "diffs": clean_diffs,
        "result": "success" if all(v == "match" for v in diffs.values()) else "fail",
    }
    return json.dumps(data, indent=2)


def merge_diff_json_fail(candidate_info):
    reference_candidates = {}
    for case_path, value in candidate_info.items():
        key = (
            str(extract_subpath_after("golden", case_path))
            if isinstance(case_path, Path) and case_path.is_absolute()
            else str(case_path)
        )
        reference_candidates[key] = value

    data = {
        "reference_case": None,
        "reference_candidates": reference_candidates,
        "result": "fail",
    }
    return json.dumps(data, indent=2)
