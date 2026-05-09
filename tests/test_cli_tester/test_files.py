# test_files.py

from textfsmgen.cli_old.tester.tester_files import (
    create_main_case_files,
    create_non_main_case_files,
)


def test_create_main_case_files(tmp_project):
    case = tmp_project / "tests" / "golden" / "main" / "demo"
    create_main_case_files(case)

    assert (case / "canonical" / "textfsm.template").is_file()
    assert (case / "inputs").is_dir()
    assert (case / "expected_results").is_dir()


def test_create_non_main_case_files(tmp_project):
    case = tmp_project / "tests" / "golden" / "category" / "demo"
    create_non_main_case_files(case)

    assert (case / "expected" / "snippet.txt").is_file()
    assert (case / "inputs").is_dir()
    assert (case / "expected_results").is_dir()
