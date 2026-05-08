# test_manifest_edit.py

from textfsmgen.cli.tester.tester_manifest import handle_tester_set
from textfsmgen.cli.tester.tester_manifest_model import load_manifest, write_manifest, Manifest
from textfsmgen.cli.tester.tester_files import create_main_case_files


def test_set_manifest_field(tmp_project, monkeypatch):
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
    rc = handle_tester_set(["demo", "meta.author", "newname"])
    assert rc == 0

    updated = load_manifest(case)
    assert updated.meta.author == "newname"
