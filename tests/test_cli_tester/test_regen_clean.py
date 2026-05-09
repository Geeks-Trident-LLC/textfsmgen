# test_regen_clean.py

from textfsmgen.cli_old.tester.tester_regen import handle_tester_regen, handle_tester_regen_all
from textfsmgen.cli_old.tester.tester_maintenance import handle_tester_clean, handle_tester_clean_all
from textfsmgen.cli_old.tester.tester_manifest_model import Manifest, write_manifest
from textfsmgen.cli_old.tester.tester_files import create_main_case_files
from textfsmgen.cli_old.tester.tester_quicktest import run_quick_test_for_case


def test_regen_and_clean(tmp_project, monkeypatch):
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
    assert handle_tester_regen(["demo"]) == 0
    assert handle_tester_clean(["demo"]) == 0
