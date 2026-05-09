# test_paths.py

from textfsmgen.cli.tester.tester_paths import (
    resolve_case_creation_path,
    resolve_case_path,
)


def test_resolve_case_creation_path_main(tmp_project, monkeypatch):
    cwd = tmp_project / "tests" / "golden" / "main"
    monkeypatch.chdir(cwd)

    path = resolve_case_creation_path("mycase", "main")
    assert path == cwd / "mycase"


def test_resolve_existing_case_path(tmp_project, monkeypatch):
    case_dir = tmp_project / "tests" / "golden" / "main" / "demo"
    case_dir.mkdir()

    monkeypatch.chdir(tmp_project)
    found = resolve_case_path("demo")
    assert found == case_dir
