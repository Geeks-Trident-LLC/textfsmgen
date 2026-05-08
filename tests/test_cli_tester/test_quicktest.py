# test_quicktest.py

from textfsmgen.cli.tester.tester_quicktest import run_quick_test_for_case
from textfsmgen.cli.tester.tester_manifest_model import Manifest, write_manifest
from textfsmgen.cli.tester.tester_files import create_main_case_files


def test_quicktest_generates_outputs(tmp_project):
    case = tmp_project / "tests" / "golden" / "main" / "demo"
    create_main_case_files(case)

    manifest = Manifest.from_flags(
        builder="category",
        category="main",
        author="tuyen",
        email="t@example.com",
        saved=False,
    )
    write_manifest(case, manifest)

    run_quick_test_for_case(case)

    assert (case / "expected_results" / "result.json").is_file()
    assert (case / "meta.json").is_file()
    assert (case / "golden.hash").is_file()
