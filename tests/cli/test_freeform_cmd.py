import json
import pytest
from click.testing import CliRunner
from textfsmgen.cli.freeform_cmd import freeform


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def patch_builder(monkeypatch, fake_freeform):
    monkeypatch.setattr(
        "textfsmgen.cli.freeform_cmd.FreeFormBuilder",
        fake_freeform,
    )


@pytest.fixture
def patch_load_sample(monkeypatch):
    monkeypatch.setattr(
        "textfsmgen.cli.shared_builder_cli.load_sample",
        lambda sf, cmd: "SAMPLE TEXT",
    )


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------


def test_freeform_help_when_no_input(runner):
    result = runner.invoke(freeform, [])
    assert result.exit_code == 0
    assert "Generate a TextFSM template" in result.output


def test_freeform_show_snippet(runner, patch_builder, patch_load_sample, tmp_path):

    result = runner.invoke(
        freeform,
        ["--snippet", "word(var_v0)", "--show", "snippet"],
    )

    assert result.exit_code == 0
    assert "word(var_v0)" in result.output


def test_freeform_debug(runner, patch_builder, patch_load_sample, tmp_path):
    snippet_path = tmp_path / "user-snippet.txt"
    snippet_path.write_text("hello")

    result = runner.invoke(
        freeform,
        ["--snippet-file", str(snippet_path), "--snippet", "x", "--debug"],
    )

    assert result.exit_code == 0
    assert f"snippet_file   = {str(snippet_path)}" in result.output


def test_freeform_create_config(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    result = runner.invoke(
        freeform,
        ["--sample-file", str(sample), "--snippet", "x", "--create-config"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["sample_file"] == str(sample)


def test_freeform_create_config_file(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

def test_freeform_create_golden_test(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    result = runner.invoke(
        freeform,
        ["--sample-file", str(sample), "--snippet", "word(var_v0)", "--create-golden-test"],
    )

    assert result.exit_code == 0
    assert "DRY-RUN" in result.output
    assert "freeform-case" in result.output


def test_freeform_create_golden_test_path(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    golden_dir = tmp_path / "golden" / "integration" / "case1"

    result = runner.invoke(
        freeform,
        [
            "--sample-file",
            str(sample),
            "--snippet",
            "word(var_v0)",
            "--create-golden-test-path",
            str(golden_dir),
        ],
    )

    assert result.exit_code == 0
    assert (golden_dir / "inputs" / "sample.txt").exists()
    assert (golden_dir / "expected" / "snippet.txt").exists()
    assert (golden_dir / "expected" / "textfsm.template").exists()
    assert (golden_dir / "expected_results" / "sample_result.json").exists()
    assert (golden_dir / "manifest.json").exists()


def test_freeform_load_config(runner, patch_builder, patch_load_sample, tmp_path):
    cfg = {
        "builder": "freeform",
        "params": {},
        "snippet": "hello",
        "snippet_file": "",
        "sample_file": "",
        "command": "",
        "show": "snippet",
        "save": "",
    }

    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text(json.dumps(cfg))

    result = runner.invoke(
        freeform,
        ["--config", str(cfg_file)],
    )

    assert result.exit_code == 0
    assert "hello" in result.output


def test_freeform_invalid_config(runner, patch_builder, patch_load_sample, tmp_path):
    cfg_file = tmp_path / "bad.json"
    cfg_file.write_text("{}")

    result = runner.invoke(
        freeform,
        ["--config", str(cfg_file)],
    )

    assert result.exit_code == 1
