"""
Implementation of:

    textfsmgen tester diff <case>

This action shows differences between expected and actual results.
"""

from __future__ import annotations

from pathlib import Path

from .shared import diff_canonical, diff_expected, diff_against_canonical
from ..core.utils import catch_path_errors
from ..core.golden_case import GoldenCase
from ..core.data_loader import extract_subpath_after


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
    tc_name = extract_subpath_after("golden", case.case_dir)

    if case.is_main():
        canonical_snippet_diff = diff_against_canonical(case, kind="snippet")
        canonical_template_diff = diff_against_canonical(case, kind="template")

        snippet_diff = diff_canonical(case, kind="snippet")
        template_diff = diff_canonical(case, kind="template")

        is_diff = (
            canonical_snippet_diff
            or canonical_template_diff
            or snippet_diff
            or template_diff
        )
    else:
        snippet_diff = diff_expected(case, kind="snippet")
        template_diff = diff_expected(case, kind="template")
        is_diff = snippet_diff or template_diff

    if not is_diff:
        print(f"[OK] {tc_name} — no differences found")
    return is_diff
