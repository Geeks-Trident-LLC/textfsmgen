import json
from click.testing import CliRunner
from textfsmgen.cli.tabular_cmd import tabular
import textfsmgen
from textfsmgen.cli.shared_builder_cli import BUILDER_MAPPING


# ------------------------------------------------------------
# --create-config-file (writes file)
# ------------------------------------------------------------


def test_create_config(runner, patch_builder, fake_tabular, tmpfile):
    patch_builder("tabular", fake_tabular)
    sample_path = tmpfile("sample.txt", "a|b|c\n1|2|3\n")

    cfg_file = sample_path.parent / "config.cfg"

    result = runner.invoke(
        tabular,
        [
            "--sample-file", str(sample_path),
            "--column-divider", "|",
            "--column-count", "3",
            "--create-config", str(cfg_file),
        ],
    )

    assert result.exit_code == 0
    assert cfg_file.exists()

    data = json.loads(cfg_file.read_text())
    assert data["params"]["column_divider"] == "|"
    assert data["params"]["column_count"] == 3


# ------------------------------------------------------------
# --create-golden-test (actual creation)
# ------------------------------------------------------------

def test_create_golden_test(runner, patch_builder, fake_tabular, tmpfile):
    patch_builder("tabular", fake_tabular)
    sample_path = tmpfile("sample.txt", "a|b|c\n1|2|3\n")

    golden_dir = sample_path.parent / "golden" / "integration" / "case1"

    result = runner.invoke(
        tabular,
        [
            "--sample-file", str(sample_path),
            "--column-divider", "|",
            "--column-count", "3",
            "--create-golden-test", str(golden_dir),
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
def test_help(runner):
    result = runner.invoke(tabular, [])
    assert result.exit_code == 1
    assert "missing required option" in result.output


# ------------------------------------------------------------
# SHOW SNIPPET
# ------------------------------------------------------------
def test_show_snippet(tmpfile, runner, patch_builder, fake_tabular):
    patch_builder("tabular", fake_tabular)

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(tabular, ["--sample-file", str(p), "--show", "snippet"])
    assert result.exit_code == 0
    assert "abc" in result.output


# ------------------------------------------------------------
# DEBUG MODE
# ------------------------------------------------------------
def test_debug(tmpfile, runner, patch_builder, fake_tabular):
    patch_builder("tabular", fake_tabular)

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
def test_params_passed(tmpfile, runner, monkeypatch, fake_tabular):
    captured = {}

    class CapturingBuilder(fake_tabular):
        def set_sample(self, sample, **params):
            super().set_sample(sample, **params)
            captured["params"] = params

    monkeypatch.setitem(
        textfsmgen.cli.shared_builder_cli.BUILDER_MAPPING,
        "tabular",
        CapturingBuilder,
    )

    p = tmpfile("sample.txt", "hello")
    runner.invoke(
        tabular,
        [
            "--sample-file", str(p),
            "--column-divider", "|",
            "--column-count", "4", "--has-header",
            "--show", "snippet",
        ],
    )
    assert captured["params"]["column_divider"] == "|"
    assert captured["params"]["column_count"] == 4
    assert captured["params"]["has_header_row"] is True


def test_column_divider_flag(tmpfile):
    runner = CliRunner()

    sample_path = tmpfile("table.txt", "a|b|c\n1|2|3\n")

    result = runner.invoke(
        tabular,
        [
            "--sample-file", str(sample_path),
            "--column-divider", "|",
            "--column-count", "3",
            "--show", "snippet",
        ],
    )

    assert result.exit_code == 0
    assert "start() " in result.output
