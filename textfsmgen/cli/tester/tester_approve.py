import shutil
from pathlib import Path
from .tester_common import find_case_root


def handle_tester_approve_results(argv):
    if not argv:
        print("error: missing case name")
        return 1

    case = argv[0]
    case_root = find_case_root(case)
    if not case_root:
        print(f"error: case not found: {case}")
        return 1

    actual_dir = case_root / "actual"
    expected_dir = case_root / "expected"

    if not actual_dir.exists():
        print("error: no actual results to approve")
        return 1

    shutil.rmtree(expected_dir, ignore_errors=True)
    shutil.copytree(actual_dir, expected_dir)

    print(f"Approved results for case: {case}")
    return 0


def handle_tester_approve_template(argv):
    if not argv:
        print("error: missing case name")
        return 1

    case = argv[0]
    case_root = find_case_root(case)
    if not case_root:
        print(f"error: case not found: {case}")
        return 1

    actual_template = case_root / "actual" / "template.textfsm"
    expected_template = case_root / "canonical" / "expected_template.textfsm"

    if not actual_template.exists():
        print("error: no actual template to approve")
        return 1

    expected_template.write_text(actual_template.read_text())

    print(f"Approved template for case: {case}")
    return 0
