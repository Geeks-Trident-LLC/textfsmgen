"""
Implementation of:

    textfsmgen tester diff <case>

This action shows differences between expected and actual results.
"""

from __future__ import annotations

from typing import List, Dict, Any

from pathlib import Path
import difflib
import json

from ..core.utils import catch_path_errors, strip_header_block
from ..core.golden_case import GoldenCase

from textfsmgen.libs.text import decorate_text
from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs.utils import get_data_as_tabular


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

@catch_path_errors
def diff(case_path: Path) -> int:
    """
    Display differences for a single golden test case.

    Returns:
        0 on no diff
        1 if any diff is found
    """
    case = GoldenCase.from_path(case_path)

    if case.is_main():
        canonical_snippet_diff = diff_against_canonical(case, kind="snippet")
        canonical_template_diff = diff_against_canonical(case, kind="template")

        snippet_diff = diff_canonical(case, kind="snippet")
        template_diff = diff_canonical(case, kind="template")

        is_diff = (canonical_snippet_diff or canonical_template_diff
                   or snippet_diff or template_diff)
    else:
        snippet_diff = diff_expected(case, kind="snippet")
        template_diff = diff_expected(case, kind="template")
        is_diff = snippet_diff or template_diff

    return is_diff


# ---------------------------------------------------------------------------
# Canonical diff
# ---------------------------------------------------------------------------

def diff_canonical(case: GoldenCase, kind: str) -> int:
    canonical = case.data.load_canonical(root="golden")
    info = canonical.get(kind)

    return diff_against_reference(
        case=case,
        ref_name=info.name,
        ref_text=info.content,
        kind=kind,
    )

# ---------------------------------------------------------------------------
# Expected diff
# ---------------------------------------------------------------------------

def diff_expected(case: GoldenCase, kind: str) -> int:
    expected = case.data.load_expected(root="golden")
    info = expected.get(kind)

    return diff_against_reference(
        case=case,
        ref_name=info.name,
        ref_text=info.content,
        kind=kind,
    )


# ---------------------------------------------------------------------------
# Shared diff logic
# ---------------------------------------------------------------------------

def diff_against_canonical(case: GoldenCase, kind: str) -> int:
    exit_code = 0
    canonical = case.data.load_canonical(root="golden")
    info = canonical.get(kind)

    ref_clean = strip_header_block(info.content)

    builder = case.data.build(canonical.sample.content)
    generated_text = getattr(builder, kind)
    generated_clean = strip_header_block(generated_text)

    diff_text = make_diff(ref_clean, generated_clean)

    if diff_text:
        exit_code = 1
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


def diff_against_reference(
    case: GoldenCase,
    ref_name: str,
    ref_text: str,
    kind: str,
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

    if groups:
        print(f"[INFO] diff-{kind} for case: {case.case_dir.name}")
        category = "canonical" if case.is_main() else "expected"
        print_block(f"Reference {kind} ({category}): {ref_name}", ref_text)

        for gen_title, gen_text, diff_title, diff_text in groups:
            print_block(gen_title, gen_text)
            print_block(diff_title, diff_text)

    return exit_code


def diff_against_canonical_result(case: GoldenCase):
    exit_code = 0
    canonical = case.data.load_canonical(root="golden")

    result = parse_textfsm_to_dicts(
        canonical.template.content,
        canonical.sample.content,
    )

    exp_result = canonical.result.content

    diff_text = make_diff_tabular(result, exp_result)

    if diff_text:
        exit_code = 1
        print(f"[INFO] canonical diff-result for case: {case.case_dir.name}")
        print_block(
            f"Diff: {canonical.result.name}\n"
            f"      vs parsed canonical sample (from {canonical.sample.name})",
            diff_text
        )
    return exit_code


def diff_against_result(case: GoldenCase):
    exit_code = 0

    if case.is_main():
        template_info = case.data.load_canonical(root="golden").template
    else:
        template_info = case.data.load_expected(root="golden").template

    for input_info, result_info in case.data.load_input_result_pairs(root="golden"):
        exp_result = result_info.content
        result = parse_textfsm_to_dicts(
            template_info.content,
            input_info.content,
        )
        diff_text = make_diff_tabular(result, exp_result)

        if diff_text:
            if not exit_code:
                print(f"[INFO] canonical diff-result for case: {case.case_dir.name}")
            exit_code = 1
            print_block(
                f"Diff: {result_info.name}\n"
                f"      vs parsed sample (from {input_info.name})",
                diff_text
            )

    return exit_code


# ----------------------------------------------------------------------------
# Diff Tabular
# ----------------------------------------------------------------------------

def make_diff_tabular(actual: List[Dict[str, Any]],
                      expected: List[Dict[str, Any]]) -> str:
    """
    Compare two parsed tabular results (list of dict rows) and return
    a human-readable diff table.

    Rules:
      1. If both tables have the same column names:
            Compare by column name; show only differing columns.
      2. If they have the same number of columns but different names:
            Compare by column index; show only differing columns.
      3. If they have different number of columns:
            Show full side-by-side tables with expected on the left
            and actual on the right.
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

# ----------------------------------------------------------------------
# CASE 1 — Compare by column name (expected first, actual second)
# ----------------------------------------------------------------------

def _diff_by_column_name(act_rows, exp_rows, columns):
    """
    Compare rows by column name and return only rows/columns
    where expected != actual.
    """
    # Identify columns that contain at least one difference
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

            if ev != av:
                row[col] = f"{ev} | {av}"
                has_diff = True
            else:
                row[col] = ""

        if has_diff:
            diff_rows.append(row)

    return get_data_as_tabular(diff_rows)

# ---------------------------------------------------------------------------
# Diff + printing helpers
# ---------------------------------------------------------------------------

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
