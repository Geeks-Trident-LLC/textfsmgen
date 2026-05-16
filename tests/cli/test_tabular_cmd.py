from textfsmgen.cli.tabular_cmd import tabular
from click.testing import CliRunner

# ------------------------------------------------------------
# HELP
# ------------------------------------------------------------
def test_tabular_help(runner):
    result = runner.invoke(tabular, [])
    assert result.exit_code == 0
    assert "Tabular builder" in result.output


# ------------------------------------------------------------
# SHOW SNIPPET
# ------------------------------------------------------------
def test_tabular_show_snippet(tmpfile, runner, monkeypatch, fake_builder):
    # Patch TabularTemplateBuilder to return fake builder
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(tabular, ["--input-file", str(p), "--show", "snippet"])

    assert result.exit_code == 0
    assert "abc" in result.output  # fake_builder.snippet = "abc"


# ------------------------------------------------------------
# DRY-RUN SAVE
# ------------------------------------------------------------
def test_tabular_save_dry_run(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        tabular, ["--input-file", str(p), "--save", "snippet-out.txt", "--dry-run"]
    )

    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output


# ------------------------------------------------------------
# DEBUG MODE
# ------------------------------------------------------------
def test_tabular_debug(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        tabular, ["--input-file", str(p), "--show", "snippet", "--debug"]
    )

    assert result.exit_code == 0
    assert "[INFO] Loaded sample" in result.output
    assert "=== DEBUG INFO ===" in result.output


# ------------------------------------------------------------
# PARAMETER PASSING
# ------------------------------------------------------------
def test_tabular_params_passed(tmpfile, runner, monkeypatch):
    captured = {}

    def fake_builder_capture(user_data, **params):  # noqa
        captured["params"] = params

        class B:
            snippet = "abc"
            template = "xyz"

        return B()

    monkeypatch.setattr(
        "textfsmgen.cli.tabular_cmd.TabularTemplateBuilder",
        fake_builder_capture,
    )

    p = tmpfile("sample.txt", "hello")

    runner.invoke(
        tabular,
        [
            "--input-file",
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

    result = runner.invoke(tabular, [   # noqa
        "--input-file", str(sample),
        "--column-divider", "|",
        "--column-count", "3",
        "--show", "snippet"
    ])

    assert result.exit_code == 0
    assert "a" in result.output
    assert "b" in result.output
