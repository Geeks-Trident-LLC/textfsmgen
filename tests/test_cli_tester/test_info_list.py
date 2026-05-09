# test_info_list.py

from textfsmgen.cli_old.tester.tester_info import handle_tester_list, handle_tester_info
from textfsmgen.cli_old.tester.tester_manifest_model import Manifest, write_manifest
from textfsmgen.cli_old.tester.tester_files import create_main_case_files


def test_list_and_info(tmp_project, monkeypatch):
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

    monkeypatch.chdir(tmp_project)
    assert handle_tester_list([]) == 0
    assert handle_tester_info(["demo"]) == 0
