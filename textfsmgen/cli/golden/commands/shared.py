from __future__ import annotations

import os
import pathlib
# ============================================================================
# Imports
# ============================================================================

import re
import difflib
import subprocess
import sys

import click
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from textfsmgen import parse_textfsm_to_dicts
from textfsmgen.libs.text import decorate_text
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs import file

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


def run_canonical(case, quicktest=False) -> int:
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
        print_status(
            f"{file.path_name(tc_name)} — failed to generate "
            f"builder from {file.path_name(canonical.sample.name)}",
            fail=True,
        )
        return 1

    # --- Snippet + Template Checks ------------------------------------------
    for kind in ("snippet", "template"):
        if diff_against_canonical(case, kind=kind, quicktest=quicktest):
            print_status(
                f"{file.path_name(tc_name)} — "
                "diff found between canonical and generated "
                f"{kind} from {file.path_name(canonical.sample.name)}",
                fail=True,
            )
            return 1

    # --- Canonical Result Check ---------------------------------------------
    if diff_against_canonical_result(case, quicktest=quicktest):
        print_status(
            f"{file.path_name(tc_name)} — diff found between "
            "canonical result and parsed result "
            f"from {file.path_name(canonical.sample.name)}",
            fail=True,
        )
        return 1

    # --- Expected Result Check (integration inputs) -------------------------
    if diff_against_result(case, quicktest=quicktest):
        print_status(
            f"{file.path_name(tc_name)} — "
            "diff found between expected and generated results",
            fail=True,
        )
        return 1

    # --- Quicktest Mode: No Writes ------------------------------------------
    if quicktest:
        print_status(f"{file.path_name(tc_name)} — quicktest completed", ok=True)
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

    print_status(
        f"{file.path_name(tc_name)} — run completed\n"
        f"  Updated: {file.path_name(meta_path)} ({meta_status})\n"
        f"  Updated: {file.path_name(hash_path)} ({hash_status})",
        ok=True,
    )
    return 0


# ============================================================================
# Expected Run Logic
# ============================================================================


def run_expected(case, quicktest=False) -> int:
    """
    Run the expected-based golden test for a case.

    Validates:
      - Snippet/template match expected
      - Parsed result matches expected
    """

    tc_name = extract_subpath_after("golden", case.case_dir)

    # --- Snippet + Template Checks ------------------------------------------
    for kind in ("snippet", "template"):
        if diff_expected(case, kind=kind, quicktest=quicktest):
            print_status(
                f"{file.path_name(tc_name)} — "
                f"diff found between expected and generated {kind}",
                fail=True,
            )
            return 1

    # --- Expected Result Check ----------------------------------------------
    if diff_against_result(case, quicktest=quicktest):
        print_status(
            f"{file.path_name(tc_name)} — "
            "diff found between expected and generated results",
            fail=True,
        )
        return 1

    # --- Success Message -----------------------------------------------------
    type_ = "quicktest" if quicktest else "run"
    print_status(f"{file.path_name(tc_name)} — {type_} completed", ok=True)
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
        col
        for col in columns
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
            has_diff |= ev != av

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


def diff_canonical(case: GoldenCase, kind: str, quicktest=False) -> int:
    canonical = case.data.load_canonical(root="golden")
    info = canonical.get(kind)

    return diff_against_reference(
        case=case,
        ref_name=info.name,
        ref_text=info.content,
        kind=kind,
        quicktest=quicktest,
    )


def diff_expected(case: GoldenCase, kind: str, quicktest=False) -> int:
    expected = case.data.load_expected(root="golden")
    info = expected.get(kind)

    return diff_against_reference(
        case=case,
        ref_name=info.name,
        ref_text=info.content,
        kind=kind,
        quicktest=quicktest,
    )


def diff_against_canonical(case: GoldenCase, kind: str, quicktest=False) -> int:
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
    if quicktest:
        return 0 if generated_clean.strip() == ref_clean.strip() else 1

    # --- Full Diff -----------------------------------------------------------
    diff_text = make_diff(ref_clean, generated_clean)
    exit_code = 1 if diff_text else 0

    if diff_text:
        print_block(f"diff-{kind} for case: {file.path_name(case.case_dir.name)}")
        print_block(
            f"Reference {kind} (canonical): {file.path_name(info.name)}", info.content
        )
        print_block(
            f"Generated {kind} from (canonical) input: {file.path_name(canonical.sample.name)}",
            generated_text,
        )
        print_block(
            f"Diff: {file.path_name(info.name)}\n"
            f"      vs generated {kind} (from {file.path_name(canonical.sample.name)})",
            diff_text,
        )
    return exit_code


# ============================================================================
# Shared Snippet/Template Diff Engine
# ============================================================================


def diff_against_reference(
    case: GoldenCase, ref_name: str, ref_text: str, kind: str, quicktest=False
) -> int:
    """
    Compare generated snippet/template against a reference (canonical or expected).
    """
    groups = []

    ref_clean = strip_header_block(ref_text)

    at_least_one_match = False

    for fileinfo in case.data.load_inputs(root="golden"):
        builder = case.data.build(fileinfo.content)
        generated_text = getattr(builder, kind)
        generated_clean = strip_header_block(generated_text)

        # --- Quicktest Fast Path ---------------------------------------------
        if quicktest:
            if generated_clean.strip() == ref_clean.strip():
                at_least_one_match = True
            continue

        # --- Full Diff -------------------------------------------------------
        diff_text = make_diff(ref_clean, generated_clean)
        if not diff_text:
            at_least_one_match = True
            continue

        groups.append(
            (
                f"Generated {kind} from input: {file.path_name(fileinfo.name)}",
                generated_text,
                f"Diff: {ref_name}\n      vs generated {kind} (from {file.path_name(fileinfo.name)})",
                diff_text,
            )
        )

    # --- Print Groups --------------------------------------------------------
    if groups:
        print_status(f"diff-{kind} for case: {file.path_name(case.case_dir.name)}")
        category = "canonical" if case.is_main() else "expected"
        print_block(
            f"Reference {kind} ({category}): {file.path_name(ref_name)}", ref_text
        )

        for gen_title, gen_text, diff_title, diff_text in groups:
            print_block(gen_title, gen_text)
            print_block(diff_title, diff_text)

    return 0 if at_least_one_match else 1


# ============================================================================
# Result Diff (Canonical + Expected)
# ============================================================================


def diff_against_canonical_result(case: GoldenCase, quicktest=False):
    canonical = case.data.load_canonical(root="golden")

    result = parse_textfsm_to_dicts(
        canonical.template.content,
        canonical.sample.content,
    )
    exp_result = canonical.result.content

    # --- Quicktest Fast Path -------------------------------------------------
    if quicktest:
        return 0 if result == exp_result else 1

    # --- Full Diff -----------------------------------------------------------
    diff_text = make_diff_tabular(result, exp_result)
    exit_code = 1 if diff_text else 0

    if diff_text:
        print_status(
            f"canonical diff-result for case: {file.path_name(case.case_dir.name)}"
        )
        print_block(
            f"Diff: {file.path_name(canonical.result.name)}\n"
            f"      vs parsed canonical sample (from {file.path_name(canonical.sample.name)})",
            diff_text,
        )
    return exit_code


def diff_against_result(case: GoldenCase, quicktest=False):
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
        if quicktest:
            if result == exp_result:
                continue
            return 1

        # --- Full Diff -------------------------------------------------------
        diff_text = make_diff_tabular(result, exp_result)

        if diff_text:
            exit_code = 1
            print_block(
                f"Diff: {file.path_name(result_info.name)}\n"
                f"      vs parsed sample (from {file.path_name(input_info.name)})",
                diff_text,
            )

    return exit_code


# ============================================================================
# Tabular Diff Utilities
# ============================================================================


def make_diff_tabular(
    actual: List[Dict[str, Any]], expected: List[Dict[str, Any]]
) -> str:
    """
    Compare two parsed tabular results (list of dict rows) and return
    a human-readable diff table.
    """

    if not expected or not actual:
        if not expected and not actual:
            return (
                "No records found in either expected or generated results. "
                "Cannot perform diff."
            )
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


_PREFIX_RE = re.compile(r"^\[[A-Z]+(-[A-Z]+)?]\s*")


def print_status(
    message: str,
    *,
    ok: bool = False,
    success: bool = False,
    fail: bool = False,
    sandbox: bool = False,
    dryrun: bool = False,
) -> None:
    """
    Print a standardized status message.

    Priority:
        1. fail=True     → [FAIL]
        2. dryrun=True   → [DRY-RUN]
        3. sandbox=True  → [SANDBOX]
        4. success=True  → [SUCCESS]
        5. ok=True       → [OK]
        6. fallback      → [INFO]
    """

    # Strip any existing prefix like [FAIL], [SUCCESS], [XYZ], etc.
    message = _PREFIX_RE.sub("", message).lstrip()

    if fail:
        print(f"[FAIL] {message}")
        return

    if dryrun:
        print(f"[DRY-RUN] {message}")
        return

    if sandbox:
        print(f"[SANDBOX] {message}")
        return

    if success:
        print(f"[SUCCESS] {message}")
        return

    if ok:
        print(f"[OK] {message}")
        return

    print(f"[INFO] {message}")


def discover_cases(base_dir):
    """
    Yield GoldenCase objects for all valid cases under base_dir.
    A valid case contains: manifest.json + inputs/
    """
    from ..core.golden_case import GoldenCase

    base_dir = Path(base_dir).resolve()

    if not base_dir.exists():
        raise click.ClickException(
            f"Directory does not exist: {file.path_name(base_dir)}"
        )

    for path in sorted(base_dir.iterdir()):
        if not path.is_dir():
            continue
        if (path / "manifest.json").exists() and (path / "inputs").exists():
            yield GoldenCase.from_path(path)


def _open_directory(path: Path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


def log(msg, *, level="info", indent=0, quiet=False, verbose=False, debug=False):
    """
    Unified logging helper with indentation, quiet mode, and debug mode.
    """
    # Quiet mode suppresses everything except FAIL and SUCCESS
    if quiet and level not in ("FAIL", "SUCCESS"):
        return

    # Debug mode prints everything
    if not debug:
        # Skip debug-only logs
        if level == "debug":
            return

        # Skip info/warn/merge logs unless verbose
        if not verbose and level in ("info", "warn", "merge"):
            return

    # Prefix formatting
    if level in ("OK", "SUCCESS", "FAIL", "DRY-RUN"):
        prefix = f"[{level}]"
    else:
        prefix = f"[{level}]"

    pad = " " * indent
    print(f"{prefix} {pad}{msg}")


def short_path(value):
    """
    Convert absolute paths to short golden-relative paths.
    """
    if isinstance(value, pathlib.Path):
        value = str(value)

    return file.path_name(value)
