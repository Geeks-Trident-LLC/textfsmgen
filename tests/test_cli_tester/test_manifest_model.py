# test_manifest_model.py

from textfsmgen.cli.tester.tester_manifest_model import (
    Manifest,
    load_manifest,
    write_manifest,
)


def test_manifest_roundtrip(tmp_project):
    case = tmp_project / "tests" / "golden" / "main" / "demo"
    case.mkdir()

    manifest = Manifest.from_flags(
        builder="category",
        category="main",
        author="tuyen",
        email="t@example.com",
        saved=False,
    )

    write_manifest(case, manifest)
    loaded = load_manifest(case)

    assert loaded.builder == "category"
    assert loaded.meta.author == "tuyen"
    assert loaded.category == "main"
