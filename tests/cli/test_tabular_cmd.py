from textfsmgen.cli.tabular_cmd import tabular
from click.testing import CliRunner


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
def test_tabular_show_snippet(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_builder,
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(tabular, ["--sample-file", str(p), "--show", "snippet"])

    assert result.exit_code == 0
    assert "abc" in result.output


# ------------------------------------------------------------
# DRY-RUN SAVE
# ------------------------------------------------------------
def test_tabular_save_dry_run(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_builder,  # <-- class, not lambda
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
def test_tabular_debug(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularBuilder",
        fake_builder,  # <-- class, not lambda
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
def test_tabular_params_passed(tmpfile, runner, monkeypatch, fake_builder):
    captured = {}

    class CapturingBuilder(fake_builder):
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
