import json
import pytest
from click.testing import CliRunner
from textfsmgen.cli.tabular_cmd import tabular


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------


@pytest.fixture
def patch_builder(monkeypatch, fake_tabular):
    """Patch TabularBuilder with FakeBuilder."""
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_tabular,
    )


# ------------------------------------------------------------
# --create-config (dry run)
# ------------------------------------------------------------


def test_tabular_create_config_dry_run(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("a|b|c\n1|2|3\n")

    result = runner.invoke(
        tabular,
        [
            "--sample-file",
            str(sample),
            "--column-divider",
            "|",
            "--column-count",
            "3",
            "--create-config",
        ],
    )

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["sample_file"] == str(sample)
    assert data["params"]["column_divider"] == "|"
    assert data["params"]["column_count"] == 3


# ------------------------------------------------------------
# --create-config-file (writes file)
# ------------------------------------------------------------


def test_tabular_create_config_file(runner, patch_builder, patch_load_sample, tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("a|b|c\n1|2|3\n")

    cfg_file = tmp_path / "tabular_cfg.json"

    result = runner.invoke(
        tabular,
        [
            "--sample-file",
            str(sample),
            "--column-divider",
            ",",
            "--column-count",
            "4",
            "--create-config-file",
            str(cfg_file),
        ],
    )

    assert result.exit_code == 0
    assert cfg_file.exists()

    data = json.loads(cfg_file.read_text())
    assert data["params"]["column_divider"] == ","
    assert data["params"]["column_count"] == 4


# ------------------------------------------------------------
# --create-golden-test (dry run)
# ------------------------------------------------------------


def test_tabular_create_golden_test_dry_run(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("a|b|c\n1|2|3\n")

    result = runner.invoke(
        tabular,
        [
            "--sample-file",
            str(sample),
            "--column-divider",
            "|",
            "--column-count",
            "3",
            "--create-golden-test",
        ],
    )

    assert result.exit_code == 0
    assert "DRY-RUN" in result.output
    assert "tabular-case" in result.output


# ------------------------------------------------------------
# --create-golden-test-path (actual creation)
# ------------------------------------------------------------


def test_tabular_create_golden_test_path(
    runner, patch_builder, patch_load_sample, tmp_path
):
    sample = tmp_path / "sample.txt"
    sample.write_text("a|b|c\n1|2|3\n")

    golden_dir = tmp_path / "golden" / "integration" / "case1"

    result = runner.invoke(
        tabular,
        [
            "--sample-file",
            str(sample),
            "--column-divider",
            "|",
            "--column-count",
            "3",
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


# ------------------------------------------------------------
# HELP
# ------------------------------------------------------------
def test_tabular_help(runner):
    result = runner.invoke(tabular, [])
    assert result.exit_code == 0
    assert "Generate a TextFSM template" in result.output


# ------------------------------------------------------------
# SHOW SNIPPET
# ------------------------------------------------------------
def test_tabular_show_snippet(tmpfile, runner, monkeypatch, fake_tabular):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_tabular,
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(tabular, ["--sample-file", str(p), "--show", "snippet"])

    assert result.exit_code == 0
    assert "abc" in result.output


# ------------------------------------------------------------
# DRY-RUN SAVE
# ------------------------------------------------------------
def test_tabular_save_dry_run(tmpfile, runner, monkeypatch, fake_tabular):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_tabular,  # <-- class, not lambda
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        tabular, ["--sample-file", str(p), "--save", "snippet-out.txt", "--dry-run"]
    )

    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output


# ------------------------------------------------------------
# DEBUG MODE
# ------------------------------------------------------------
def test_tabular_debug(tmpfile, runner, monkeypatch, fake_tabular):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_tabular,  # <-- class, not lambda
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        tabular, ["--sample-file", str(p), "--show", "snippet", "--debug"]
    )

    assert result.exit_code == 0
    assert "[INFO] Loaded sample" in result.output
    assert "=== DEBUG INFO ===" in result.output


# ------------------------------------------------------------
# PARAMETER PASSING
# ------------------------------------------------------------
def test_tabular_params_passed(tmpfile, runner, monkeypatch, fake_tabular):
    captured = {}

    class CapturingBuilder(fake_tabular):
        def set_sample(self, sample, **params):
            super().set_sample(sample, **params)
            captured["params"] = params

    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        CapturingBuilder,
    )

    p = tmpfile("sample.txt", "hello")

    runner.invoke(
        tabular,
        [
            "--sample-file",
            str(p),
            "--column-divider",
            "|",
            "--column-count",
            "4",
            "--has-header",
            "--show",
            "snippet",
        ],
    )

    assert captured["params"]["column_divider"] == "|"
    assert captured["params"]["column_count"] == 4
    assert captured["params"]["has_header_row"] is True


def test_tabular_column_divider_flag(tmp_path):
    runner = CliRunner()

    sample = tmp_path / "table.txt"
    sample.write_text("a|b|c\n1|2|3\n")

    result = runner.invoke(
        tabular,
        [  # noqa
            "--sample-file",
            str(sample),
            "--column-divider",
            "|",
            "--column-count",
            "3",
            "--show",
            "snippet",
        ],
    )

    assert result.exit_code == 0
    assert "a" in result.output
    assert "b" in result.output
