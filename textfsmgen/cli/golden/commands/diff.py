from __future__ import annotations

import json
from pathlib import Path
import difflib

from textfsmgen import parse_textfsm_to_dicts
from textfsmgen.libs.generic import DotDict
from textfsmgen.libs import file

from .shared import print_status
from ..core.utils import catch_path_errors
from ..core.golden_case import GoldenCase
from ..core.data_loader import extract_subpath_after


# ---------------------------------------------------------------------------
# Diff Item Model
# ---------------------------------------------------------------------------

class DiffItem(DotDict):
    """
    Represents a single diff result.

    Fields:
        name: short relative name (e.g. expected/snippet.txt)
        expected: expected text or JSON
        generated: generated text or JSON
        diff_text: unified diff text
        passed: True if no diff
        reason: explanation
    """
    pass


# ---------------------------------------------------------------------------
# Unified diff helpers
# ---------------------------------------------------------------------------

def make_unified_diff(expected: str, generated: str,
                      *, fromfile="expected", tofile="generated") -> str:
    diff = difflib.unified_diff(
        expected.splitlines(keepends=True),
        generated.splitlines(keepends=True),
        fromfile=fromfile,
        tofile=tofile,
        lineterm="",
    )
    return "".join(diff)


def make_json_diff(expected_list: list, generated_list: list, unified: int) -> str:
    left = json.dumps(expected_list[:unified], indent=2, ensure_ascii=False, sort_keys=True)
    right = json.dumps(generated_list[:unified], indent=2, ensure_ascii=False, sort_keys=True)
    return make_unified_diff(left, right)


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

def print_diff_item(item: DiffItem, *, names_only=False, verbose=False):
    """Print a diff item according to flags."""
    if item.passed:
        if verbose:
            print_status(f"{item.name} — no differences", ok=True)
        return

    if names_only:
        print_status(f"DIFF: {item.name}", fail=True)
        return

    print_status(f"DIFF: {item.name}", fail=True)
    print(item.diff_text)


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

@catch_path_errors
def diff(
        case_path: Path, names_only=False, diff_type="all", unified=3,
        json_output=False, summary=False, fail_on_diff=False, verbose=False
) -> int:
    """
    Display differences for a single golden test case.

    Returns:
        0 on no diff
        1 if any diff is found
    """
    case = GoldenCase.from_path(case_path)
    tc_name = extract_subpath_after("golden", case.case_dir)

    items: list[DiffItem] = []

    # MAIN CASE
    if case.is_main():
        if diff_type in ("all", "snippet"):
            items.append(diff_canonical_snippet(case))
        if diff_type in ("all", "template"):
            items.append(diff_canonical_template(case))
        if diff_type in ("all", "result"):
            items.append(diff_canonical_result(case, unified=unified))
        if diff_type in ("all", "results"):
            items.extend(diff_results_using_canonical_template(case, unified=unified))

    # INTEGRATION CASE
    else:
        if diff_type in ("all", "snippet"):
            items.extend(diff_expected_snippet(case))
        if diff_type in ("all", "template"):
            items.extend(diff_expected_template(case))
        if diff_type in ("all", "results"):
            items.extend(diff_results_using_expected_template(case, unified=unified))

    # Determine diff status
    any_diff = any(not item.passed for item in items)

    # JSON output mode
    if json_output:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 1 if any_diff and fail_on_diff else 0

    # Print items
    for item in items:
        print_diff_item(item, names_only=names_only, verbose=verbose)

    # Summary mode
    if summary:
        total = len(items)
        failed = sum(1 for i in items if not i.passed)
        passed = total - failed
        print_status(f"Summary: {passed}/{total} passed, {failed} failed",
                     ok=(failed == 0), fail=(failed > 0))

    # Final no-diff message
    if not any_diff:
        print_status(f"{tc_name} — no differences found", ok=True)

    # Fail-on-diff behavior
    return 1 if any_diff and fail_on_diff else 0


# ---------------------------------------------------------------------------
# MAIN CASE DIFFS
# ---------------------------------------------------------------------------

def diff_canonical_snippet(case: GoldenCase) -> DiffItem:
    canonical = case.data.load_canonical("golden")

    expected = canonical.snippet.content
    sample = canonical.sample.content

    builder = case.data.build(sample=sample)
    if not builder:
        return DiffItem(
            name=canonical.snippet.name,
            expected=expected,
            generated="",
            diff_text="",
            passed=False,
            reason=f"Failed to build snippet from sample {canonical.sample.name}",
        )

    generated = builder.snippet
    diff_text = make_unified_diff(expected, generated)

    return DiffItem(
        name=canonical.snippet.name,
        expected=expected,
        generated=generated,
        diff_text=diff_text,
        passed=(diff_text == ""),
        reason="No diff" if diff_text == "" else "Diff found",
    )


def diff_canonical_template(case: GoldenCase) -> DiffItem:
    canonical = case.data.load_canonical("golden")

    expected = canonical.template.content
    sample = canonical.sample.content

    builder = case.data.build(sample=sample)
    if not builder:
        return DiffItem(
            name=canonical.template.name,
            expected=expected,
            generated="",
            diff_text="",
            passed=False,
            reason=f"Failed to build template from sample {canonical.sample.name}",
        )

    generated = builder.template
    diff_text = make_unified_diff(expected, generated)

    return DiffItem(
        name=canonical.template.name,
        expected=expected,
        generated=generated,
        diff_text=diff_text,
        passed=(diff_text == ""),
        reason="No diff" if diff_text == "" else "Diff found",
    )


def diff_canonical_result(case: GoldenCase, unified=3) -> DiffItem:
    canonical = case.data.load_canonical("golden")

    expected = canonical.result.content
    sample = canonical.sample.content
    template = canonical.template.content

    generated = parse_textfsm_to_dicts(template, sample)
    diff_text = make_json_diff(expected, generated, unified)

    return DiffItem(
        name=canonical.result.name,
        expected=expected,
        generated=generated,
        diff_text=diff_text,
        passed=(diff_text == ""),
        reason="No diff" if diff_text == "" else "Diff found",
    )


def diff_results_using_canonical_template(case: GoldenCase, unified=3):
    items = []
    canonical = case.data.load_canonical("golden")
    template = canonical.template.content
    for inp, res in case.data.load_input_result_pairs("golden"):
        expected = res.content
        generated = parse_textfsm_to_dicts(template, inp.content)
        diff_text = make_json_diff(expected, generated, unified)

        items.append(DiffItem(
            name=res.name,
            expected=expected,
            generated=generated,
            diff_text=diff_text,
            passed=(diff_text == ""),
            reason="No diff" if diff_text == "" else "Diff found",
        ))

    return items


# ---------------------------------------------------------------------------
# INTEGRATION CASE DIFFS
# ---------------------------------------------------------------------------

def diff_expected_snippet(case: GoldenCase):
    items = []
    expected = case.data.load_expected("golden")
    for inp in case.data.load_inputs("golden"):
        builder = case.data.build(sample=inp.content)
        if not builder:
            items.append(DiffItem(
                name=expected.snippet.name,
                expected=expected.snippet.content,
                generated="",
                diff_text="",
                passed=False,
                reason=f"Failed to build snippet from sample {inp.name}",
            ))
            continue

        generated = builder.snippet
        diff_text = make_unified_diff(expected.snippet.content, generated)

        items.append(DiffItem(
            name=expected.snippet.name,
            expected=expected.snippet.content,
            generated=generated,
            diff_text=diff_text,
            passed=(diff_text == ""),
            reason="No diff" if diff_text == "" else "Diff found",
        ))
    return items


def diff_expected_template(case: GoldenCase):
    items = []
    expected = case.data.load_expected("golden")
    for inp in case.data.load_inputs("golden"):
        builder = case.data.build(sample=inp.content)
        if not builder:
            items.append(DiffItem(
                name=expected.template.name,
                expected=expected.template.content,
                generated="",
                diff_text="",
                passed=False,
                reason=f"Failed to build template from sample {inp.name}",
            ))
            continue

        generated = builder.template
        diff_text = make_unified_diff(expected.template.content, generated)

        items.append(DiffItem(
            name=expected.template.name,
            expected=expected.template.content,
            generated=generated,
            diff_text=diff_text,
            passed=(diff_text == ""),
            reason="No diff" if diff_text == "" else "Diff found",
        ))
    return items


def diff_results_using_expected_template(case: GoldenCase, unified=3):
    items = []
    expected = case.data.load_expected("golden")
    template = expected.template.content
    for inp, res in case.data.load_input_result_pairs("golden"):
        generated = parse_textfsm_to_dicts(template, inp.content)
        diff_text = make_json_diff(res.content, generated, unified)

        items.append(DiffItem(
            name=res.name,
            expected=res.content,
            generated=generated,
            diff_text=diff_text,
            passed=(diff_text == ""),
            reason="No diff" if diff_text == "" else "Diff found",
        ))
    return items
