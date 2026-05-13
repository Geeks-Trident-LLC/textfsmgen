import json

from textfsmgen.libs.common import parse_textfsm_to_dicts, extract_textfsm_headers
from ..core.golden_case import GoldenCase
from ..core.data_loader import extract_subpath_after


def run_identical(case_dirs, compact=False, is_json=False):

    cases = [GoldenCase.from_path(p) for p in case_dirs]

    # mapping: case_name -> list of identical cases
    mapping = {str(c.case_dir): [str(c.case_dir)] for c in cases}

    # ------------------------------------------------------------
    # Outer loop: choose reference template
    # ------------------------------------------------------------
    for outer in cases:
        outer_template = outer.data.load_expected().template.content
        outer_columns = set(extract_textfsm_headers(outer_template))

        # --------------------------------------------------------
        # Inner loop: compare with every other case
        # --------------------------------------------------------
        for inner in cases:
            if inner is outer:
                continue

            if _cases_are_identical(inner, outer_template, outer_columns):
                mapping[str(outer.case_dir)].append(str(inner.case_dir))

    # ------------------------------------------------------------
    # Extract unique groups
    # ------------------------------------------------------------
    groups = _extract_identical_groups(mapping)

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------
    if is_json:
        return _print_json(groups)

    if compact:
        return _print_compact(groups)

    return _print_normal(groups)


# ======================================================================
# INTERNAL HELPERS
# ======================================================================

def _cases_are_identical(inner, outer_template, outer_columns):
    """
    True if:
    - outer template parses all inner inputs
    - parsed rows == inner expected rows
    - column sets match
    """
    for inp, res in inner.data.load_input_result_pairs():
        sample = inp.content
        expected_rows = res.content
        try:
            rows = parse_textfsm_to_dicts(outer_template, sample)
        except Exception:   # noqa
            return False

        if not expected_rows or not rows:
            return False

        # Compare row content
        if rows != expected_rows:
            return False

        # Compare columns
        if not _columns_match(rows, expected_rows, outer_columns):
            return False

    return True


def _columns_match(rows, expected_rows, outer_columns):
    """
    Ensure that:
    - outer template columns == expected columns
    - and rows contain only those columns
    """
    if not expected_rows:
        return True

    expected_cols = set(expected_rows[0].keys())
    if expected_cols != outer_columns:
        return False

    for r in rows:
        if set(r.keys()) != expected_cols:
            return False

    return True


def _extract_identical_groups(mapping):
    """
    Convert mapping:
        { "a": ["a", "b"], "b": ["b"], "c": ["c"] }
    into unique groups:
        [["a", "b"]]
    """
    seen = set()
    groups = []

    for key, group in mapping.items():
        g = tuple(sorted(group))
        if len(g) < 2:
            continue
        if g not in seen:
            seen.add(g)
            groups.append(list(g))

    return groups


# ======================================================================
# OUTPUT MODES
# ======================================================================

def _print_normal(groups):
    if not groups:
        print("[IDENTICAL] No identical cases found.")
        return

    print("[IDENTICAL] Identical case groups:")
    for group in groups:
        clean_grp = [str(extract_subpath_after("golden", item)) for item in group]
        print("  - " + ", ".join(clean_grp))


def _print_compact(groups):
    count = len(groups)
    print(f"[IDENTICAL] Groups: {count}")
    if count > 0:
        print("[IDENTICAL] Result: identical")
    else:
        print("[IDENTICAL] Result: distinct")


def _print_json(groups):
    clean_groups = []
    for group in groups:
        clean_grp = [str(extract_subpath_after("golden", item)) for item in group]
        clean_groups.append(clean_grp)

    obj = {"identical_groups": clean_groups}
    print(json.dumps(obj, indent=2))
