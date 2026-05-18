import json
import pytest
from textfsmgen import FreeFormBuilder
from textfsmgen.cli.shared_builder_cli import dry_run_or_create_golden_test


# ------------------------------------------------------------
# Mock builder + BuildResult
# ------------------------------------------------------------
class MockBuildResult:
    def __init__(self):
        self.sample = "SAMPLE TEXT"
        self.snippet = "SNIPPET"
        self.template = "TEMPLATE"
        self.result = {"ok": True}
        self.warning = ""


class MockBuilder(FreeFormBuilder):
    def set_sample(self, sample, **params):
        self.sample = sample

    def set_snippet(self, snippet):
        self.snippet = snippet

    def set_snippet_file(self, path):
        self.snippet = f"FILE:{path}"

    def build(self):
        pass

    def to_result(self):
        return MockBuildResult()


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------


def test_golden_test_dry_run(capsys, monkeypatch):
    monkeypatch.setattr(
        "textfsmgen.cli.shared_builder_cli.load_sample",
        lambda sf, cmd: "SAMPLE TEXT",
    )

    with pytest.raises(SystemExit) as exc:
        dry_run_or_create_golden_test(
            builder_class=MockBuilder,
            builder_name="freeform",
            golden_path="",  # dry run
            params={},
            snippet="word(var_v0)",
            snippet_file="",
            sample_file="dummy.txt",
            command="",  # load_sample will be mocked below
        )

    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "freeform-case" in out


def test_golden_test_create(tmp_path, monkeypatch):
    # Patch load_sample to return a sample
    monkeypatch.setattr(
        "textfsmgen.cli.shared_builder_cli.load_sample",
        lambda sf, cmd: "SAMPLE TEXT",
    )

    golden_root = tmp_path / "tests" / "golden" / "integration" / "case1"
    golden_path = str(golden_root)

    with pytest.raises(SystemExit) as exc:
        dry_run_or_create_golden_test(
            builder_class=MockBuilder,
            builder_name="freeform",
            golden_path=golden_path,
            params={},
            snippet="word(var_v0)",
            snippet_file="",
            sample_file="dummy.txt",
            command="",
        )

    assert exc.value.code == 0

    # Validate files
    assert (golden_root / "inputs" / "sample.txt").exists()
    assert (golden_root / "expected" / "snippet.txt").exists()
    assert (golden_root / "expected" / "textfsm.template").exists()
    assert (golden_root / "expected_results" / "sample_result.json").exists()
    assert (golden_root / "manifest.json").exists()

    manifest = json.loads((golden_root / "manifest.json").read_text())
    assert manifest["builder"] == "freeform"


def test_golden_test_rejects_wrong_path(tmp_path, capsys):
    wrong_path = tmp_path / "not" / "allowed"

    with pytest.raises(SystemExit) as exc:
        dry_run_or_create_golden_test(
            builder_class=MockBuilder,
            builder_name="freeform",
            golden_path=str(wrong_path),
            params={},
            snippet="word(var_v0)",
            snippet_file="",
            sample_file="dummy.txt",
            command="",
        )

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "must be inside" in out


def test_golden_test_requires_sample(monkeypatch, capsys):
    # Force load_sample to return empty
    monkeypatch.setattr(
        "textfsmgen.cli.shared_builder_cli.load_sample",
        lambda sf, cmd: "",
    )

    with pytest.raises(SystemExit) as exc:
        dry_run_or_create_golden_test(
            builder_class=MockBuilder,
            builder_name="freeform",
            golden_path="",
            params={},
            snippet="word(var_v0)",
            snippet_file="",
            sample_file="dummy.txt",
            command="",
        )

    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "requires a non-empty sample" in out
