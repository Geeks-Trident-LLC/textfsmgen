# test_preview.py

from textfsmgen.cli_old.tester.tester_preview import handle_tester_preview
from textfsmgen.cli_old.tester.tester_manifest_model import Manifest, write_manifest
from textfsmgen.cli_old.tester.tester_files import create_main_case_files
from textfsmgen.cli_old.tester.tester_quicktest import run_quick_test_for_case


def test_preview_results(tmp_project, monkeypatch):
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
    rc = handle_tester_preview(["preview-results", "demo"])
    assert rc == 0
