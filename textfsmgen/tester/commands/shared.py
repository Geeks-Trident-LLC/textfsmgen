from __future__ import annotations

# ============================================================================
# Imports
# ============================================================================

import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from textfsmgen import parse_textfsm_to_dicts
from textfsmgen.libs.text import decorate_text
from textfsmgen.libs.utils import get_data_as_tabular

from ..core.data_loader import extract_subpath_after
from ..core.golden_case import GoldenCase
from ..core.utils import strip_header_block


# ============================================================================
# File Status Helpers
# ============================================================================

def describe_file_update(path: Path, exist=False) -> str:
    """
    Return a human-readable status string:
      - 'created at <timestamp>' if file did not exist before
      - 'modified at <timestamp>' if file existed
    """
    if not exist:
        return f"created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return f"modified at {mtime.strftime('%Y-%m-%d %H:%M:%S')}"


# ============================================================================
# Canonical Run Logic
# ============================================================================

def run_canonical(case, is_quicktest=False) -> int:
    """
    Run the canonical golden test for a case.

    Validates:
      - Builder generation
      - Snippet/template match canonical
      - Parsed result matches canonical
      - Writes meta + hash (only when not quicktest)
    """

    tc_name = extract_subpath_after("golden", case.case_dir)

    # --- Builder validation --------------------------------------------------
    canonical = case.data.load_canonical(root="golden")
    builder = case.data.build(sample=canonical.sample.content)

    if not builder:
        print(f"[FAIL] {tc_name} — failed to generate builder from {canonical.sample.name}")
        return 1

    # --- Snippet + Template Checks ------------------------------------------
    for kind in ("snippet", "template"):
        if diff_against_canonical(case, kind=kind, is_quicktest=is_quicktest):
            print(
                f"[FAIL] {tc_name} — diff found between canonical and generated "
                f"{kind} from {canonical.sample.name}"
            )
            return 1

    # --- Canonical Result Check ---------------------------------------------
    if diff_against_canonical_result(case, is_quicktest=is_quicktest):
        print(
            f"[FAIL] {tc_name} — diff found between canonical result and parsed result "
            f"from {canonical.sample.name}"
        )
        return 1

    # --- Expected Result Check (integration inputs) -------------------------
    if diff_against_result(case, is_quicktest=is_quicktest):
        print(f"[FAIL] {tc_name} — diff found between expected and generated results")
        return 1

    # --- Quicktest Mode: No Writes ------------------------------------------
    if is_quicktest:
        print(f"[OK] {tc_name} — quicktest completed")
        return 0

    # --- Full Run: Write meta.json + golden.hash ----------------------------
    meta_path = Path(case.case_dir) / "meta.json"
    hash_path = Path(case.case_dir) / "golden.hash"

    meta_status_before = meta_path.exists()
    hash_status_before = hash_path.exists()

    case.data.write_meta()
    case.data.write_golden_hash()

    meta_status = describe_file_update(meta_path, exist=meta_status_before)
    hash_status = describe_file_update(hash_path, exist=hash_status_before)

    print(
        f"[OK] {tc_name} — run completed\n"
        f"  Updated: {meta_path} ({meta_status})\n"
        f"  Updated: {hash_path} ({hash_status})\n"
    )
    return 0


# ============================================================================
# Expected Run Logic
# ============================================================================

def run_expected(case, is_quicktest=False) -> int:
    """
    Run the expected-based golden test for a case.

    Validates:
      - Snippet/template match expected
      - Parsed result matches expected
    """

    tc_name = extract_subpath_after("golden", case.case_dir)

    # --- Snippet + Template Checks ------------------------------------------
    for kind in ("snippet", "template"):
        if diff_expected(case, kind=kind, is_quicktest=is_quicktest):
            print(f"[FAIL] {tc_name} — diff found between expected and generated {kind}")
            return 1

    # --- Expected Result Check ----------------------------------------------
    if diff_against_result(case, is_quicktest=is_quicktest):
        print(f"[FAIL] {tc_name} — diff found between expected and generated results")
        return 1

    # --- Success Message -----------------------------------------------------
    type_ = "quicktest" if is_quicktest else "run"
    print(f"[OK] {tc_name} — {type_} completed")
    return 0


# ============================================================================
# Diff: Column-Based Tabular Comparison
# ============================================================================

def _diff_by_column_name(act_rows, exp_rows, columns):
    """
    Compare rows by column name and return only rows/columns
    where expected != actual.
    """
    diff_cols = [
        col for col in columns
        if any(a.get(col) != e.get(col) for a, e in zip(act_rows, exp_rows))
    ]

    if not diff_cols:
        return ""

    diff_rows = []

    for idx, (a, e) in enumerate(zip(act_rows, exp_rows), start=1):
        row = {"index": str(idx)}
        has_diff = False

        for col in diff_cols:
            ev = e.get(col, "")
            av = a.get(col, "")
            row[col] = f"{ev} | {av}" if ev != av else ""
            has_diff |= (ev != av)

        if has_diff:
            diff_rows.append(row)

    return get_data_as_tabular(diff_rows)


# ============================================================================
# Diff Printing Helpers
# ============================================================================

def make_diff(left: str, right: str) -> str:
    diff_ = difflib.unified_diff(
        left.splitlines(keepends=True),
        right.splitlines(keepends=True),
        fromfile="expected",
        tofile="generated",
        lineterm="",
    )
    return "".join(diff_)


def print_block(title: str, content: str):
    print(decorate_text(title))
    print(content.rstrip() if content.strip() else "(empty)")
    print()


# ============================================================================
# Snippet/Template Diff APIs
# ============================================================================

def diff_canonical(case: GoldenCase, kind: str, is_quicktest=False) -> int:
    canonical = case.data.load_canonical(root="golden")
    info = canonical.get(kind)

    return diff_against_reference(
        case=case,
        ref_name=info.name,
        ref_text=info.content,
        kind=kind,
        is_quicktest=is_quicktest
    )


def diff_expected(case: GoldenCase, kind: str, is_quicktest=False) -> int:
    expected = case.data.load_expected(root="golden")
    info = expected.get(kind)

    return diff_against_reference(
        case=case,
        ref_name=info.name,
        ref_text=info.content,
        kind=kind,
        is_quicktest=is_quicktest
    )


def diff_against_canonical(case: GoldenCase, kind: str, is_quicktest=False) -> int:
    """
    Public API: Compare generated <kind> against canonical reference.
    """
    canonical = case.data.load_canonical(root="golden")
    info = canonical.get(kind)

    ref_clean = strip_header_block(info.content)

    builder = case.data.build(canonical.sample.content)
    generated_text = getattr(builder, kind)
    generated_clean = strip_header_block(generated_text)

    # --- Quicktest Fast Path -------------------------------------------------
    if is_quicktest:
        return 0 if generated_clean.strip() == ref_clean.strip() else 1

    # --- Full Diff -----------------------------------------------------------
    diff_text = make_diff(ref_clean, generated_clean)
    exit_code = 1 if diff_text else 0

    if diff_text:
        print(f"[INFO] diff-{kind} for case: {case.case_dir.name}")
        print_block(f"Reference {kind} (canonical): {info.name}", info.content)
        print_block(
            f"Generated {kind} from (canonical) input: {canonical.sample.name}",
            generated_text
        )
        print_block(
            f"Diff: {info.name}\n"
            f"      vs generated {kind} (from {canonical.sample.name})",
            diff_text
        )
    return exit_code


# ============================================================================
# Shared Snippet/Template Diff Engine
# ============================================================================

def diff_against_reference(
    case: GoldenCase,
    ref_name: str,
    ref_text: str,
    kind: str,
    is_quicktest=False
) -> int:
    """
    Compare generated snippet/template against a reference (canonical or expected).
    """
    groups = []
    exit_code = 0

    ref_clean = strip_header_block(ref_text)

    for fileinfo in case.data.load_inputs(root="golden"):
        builder = case.data.build(fileinfo.content)
        generated_text = getattr(builder, kind)
        generated_clean = strip_header_block(generated_text)

        # --- Quicktest Fast Path ---------------------------------------------
        if is_quicktest:
            if generated_clean.strip() == ref_clean.strip():
                continue
            return 1

        # --- Full Diff -------------------------------------------------------
        diff_text = make_diff(ref_clean, generated_clean)
        if diff_text:
            exit_code = 1
            groups.append(
                (
                    f"Generated {kind} from input: {fileinfo.name}",
                    generated_text,
                    f"Diff: {ref_name}\n"
                    f"      vs generated {kind} (from {fileinfo.name})",
                    diff_text,
                )
            )

    # --- Print Groups --------------------------------------------------------
    if groups:
        print(f"[INFO] diff-{kind} for case: {case.case_dir.name}")
        category = "canonical" if case.is_main() else "expected"
        print_block(f"Reference {kind} ({category}): {ref_name}", ref_text)

        for gen_title, gen_text, diff_title, diff_text in groups:
            print_block(gen_title, gen_text)
            print_block(diff_title, diff_text)

    return exit_code


# ============================================================================
# Result Diff (Canonical + Expected)
# ============================================================================

def diff_against_canonical_result(case: GoldenCase, is_quicktest=False):
    canonical = case.data.load_canonical(root="golden")

    result = parse_textfsm_to_dicts(
        canonical.template.content,
        canonical.sample.content,
    )
    exp_result = canonical.result.content

    # --- Quicktest Fast Path -------------------------------------------------
    if is_quicktest:
        return 0 if result == exp_result else 1

    # --- Full Diff -----------------------------------------------------------
    diff_text = make_diff_tabular(result, exp_result)
    exit_code = 1 if diff_text else 0

    if diff_text:
        print(f"[INFO] canonical diff-result for case: {case.case_dir.name}")
        print_block(
            f"Diff: {canonical.result.name}\n"
            f"      vs parsed canonical sample (from {canonical.sample.name})",
            diff_text
        )
    return exit_code


def diff_against_result(case: GoldenCase, is_quicktest=False):
    exit_code = 0

    # Choose template source
    if case.is_main():
        template_info = case.data.load_canonical(root="golden").template
    else:
        template_info = case.data.load_expected(root="golden").template

    # Iterate over input/result pairs
    for input_info, result_info in case.data.load_input_result_pairs(root="golden"):
        exp_result = result_info.content
        result = parse_textfsm_to_dicts(
            template_info.content,
            input_info.content,
        )

        # --- Quicktest Fast Path ---------------------------------------------
        if is_quicktest:
            if result == exp_result:
                continue
            return 1

        # --- Full Diff -------------------------------------------------------
        diff_text = make_diff_tabular(result, exp_result)

        if diff_text:
            exit_code = 1
            print_block(
                f"Diff: {result_info.name}\n"
                f"      vs parsed sample (from {input_info.name})",
                diff_text
            )

    return exit_code


# ============================================================================
# Tabular Diff Utilities
# ============================================================================

def make_diff_tabular(actual: List[Dict[str, Any]],
                      expected: List[Dict[str, Any]]) -> str:
    """
    Compare two parsed tabular results (list of dict rows) and return
    a human-readable diff table.
    """

    if not expected or not actual:
        if not expected and not actual:
            return ("No records found in either expected or generated results. "
                    "Cannot perform diff.")
        if not expected:
            return "No records found in expected results. Cannot perform diff."
        return "No records found in generated results. Cannot perform diff."

    cols_actual = set(actual[0].keys()) if actual else set()
    cols_expected = set(expected[0].keys()) if expected else set()

    if cols_actual != cols_expected:
        headers_act = ", ".join(actual[0].keys())
        headers_exp = ", ".join(expected[0].keys())
        return (
            "Column mismatch detected. Cannot perform diff.\n"
            f"Expected columns : {headers_exp}\n"
            f"Actual columns   : {headers_act}\n"
        )

    max_rows = max(len(actual), len(expected))
    act_rows = actual + [{}] * (max_rows - len(actual))
    exp_rows = expected + [{}] * (max_rows - len(expected))

    exp_cols = list(exp_rows[0].keys()) if exp_rows else []

    return _diff_by_column_name(act_rows, exp_rows, exp_cols)


def have_same_columns(list_a, list_b):
    """
    Return True if two list-of-dict tables have the same columns.
    Empty lists are treated as having no columns.
    """
    cols_a = set(list_a[0].keys()) if list_a else set()
    cols_b = set(list_b[0].keys()) if list_b else set()
    return cols_a == cols_b and cols_a
