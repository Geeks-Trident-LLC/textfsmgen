import json
import pytest
from click.testing import CliRunner
from textfsmgen.cli.category_cmd import category


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------


@pytest.fixture
def patch_builder(monkeypatch, fake_category):
    """Patch CategoryBuilder with FakeBuilder."""
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryBuilder",
        fake_category,
    )


# ------------------------------------------------------------
# --create-config (dry run)
# ------------------------------------------------------------


def test_category_create_config(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    result = runner.invoke(
        category,
        [
            "--sample-file",
            str(sample),
            "--count",
            "3",
            "--separator",
            ":",
            "--create-config",
        ],
    )

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["sample_file"] == str(sample)
    assert data["params"]["count"] == 3
    assert data["params"]["separator"] == ":"


# ------------------------------------------------------------
# --create-config-file (writes file)
# ------------------------------------------------------------


def test_category_create_config_file(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    cfg_file = tmp_path / "category_cfg.json"

    result = runner.invoke(
        category,
        [
            "--sample-file",
            str(sample),
            "--count",
            "2",
            "--separator",
            "=",
            "--create-config-file",
            str(cfg_file),
        ],
    )

    assert result.exit_code == 0
    assert cfg_file.exists()

    data = json.loads(cfg_file.read_text())
    assert data["params"]["count"] == 2
    assert data["params"]["separator"] == "="


# ------------------------------------------------------------
# --create-golden-test (dry run)
# ------------------------------------------------------------


def test_category_create_golden_test(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    result = runner.invoke(
        category,
        [
            "--sample-file",
            str(sample),
            "--count",
            "1",
            "--create-golden-test",
        ],
    )

    assert result.exit_code == 0
    assert "DRY-RUN" in result.output
    assert "category-case" in result.output


# ------------------------------------------------------------
# --create-golden-test-path (actual creation)
# ------------------------------------------------------------


def test_category_create_golden_test_path(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("hello")

    golden_dir = tmp_path / "golden" / "integration" / "case1"

    result = runner.invoke(
        category,
        [
            "--sample-file",
            str(sample),
            "--count",
            "1",
            "--create-golden-test-path",
            str(golden_dir),
        ],
    )

    assert result.exit_code == 0

    # Validate golden test structure
    assert (golden_dir / "inputs" / "sample.txt").exists()
    assert (golden_dir / "expected" / "snippet.txt").exists()
    assert (golden_dir / "expected" / "textfsm.template").exists()
    assert (golden_dir / "expected_results" / "sample_result.json").exists()
    assert (golden_dir / "manifest.json").exists()


def test_category_help(runner):
    result = runner.invoke(category, [])
    assert result.exit_code == 0
    assert "Generate a TextFSM template" in result.output


def test_category_show_snippet(tmpfile, runner, monkeypatch, fake_category):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryBuilder",
        fake_category,  # <-- class, not lambda
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(category, ["--sample-file", str(p), "--show", "snippet"])

    assert result.exit_code == 0
    assert "abc" in result.output


def test_category_debug(tmpfile, runner, monkeypatch, fake_category):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryBuilder",
        fake_category,
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        category, ["--sample-file", str(p), "--show", "snippet", "--debug"]
    )

    assert result.exit_code == 0
    assert "[INFO] Loaded sample" in result.output
    assert "=== DEBUG INFO ===" in result.output


def test_category_sample_file_flag(tmp_path):
    runner = CliRunner()

    sample = tmp_path / "sample.txt"
    sample.write_text("key: value\n")

    result = runner.invoke(
        category,
        [  # noqa
            "--sample-file",
            str(sample),
            "--show",
            "sample",
        ],
    )

    assert result.exit_code == 0
    assert "key: value" in result.output


def test_category_debug_print_shows_sample_file(tmp_path):
    runner = CliRunner()

    sample = tmp_path / "sample.txt"
    sample.write_text("alpha: beta\n", encoding="utf-8")

    result = runner.invoke(
        category, ["--sample-file", str(sample), "--show", "sample", "--debug"]
    )

    assert result.exit_code == 0
    assert "sample_file    =" in result.output
    assert "[DEBUG]" in result.output or "DEBUG" in result.output
