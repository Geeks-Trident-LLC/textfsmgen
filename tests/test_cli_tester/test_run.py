# test_run.py

from textfsmgen.cli.tester.tester_run import handle_tester_run
from textfsmgen.cli.tester.tester_manifest_model import Manifest, write_manifest
from textfsmgen.cli.tester.tester_files import create_main_case_files
from textfsmgen.cli.tester.tester_quicktest import run_quick_test_for_case


def test_run_ok(tmp_project, monkeypatch):
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

    monkeypatch.chdir(tmp_project)
    rc = handle_tester_run(["demo"])
    assert rc == 0
