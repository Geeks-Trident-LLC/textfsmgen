from click.testing import CliRunner
from textfsmgen.cli.category_cmd import category


def test_category_help(runner):
    result = runner.invoke(category, [])
    assert result.exit_code == 0
    assert "Category builder" in result.output


def test_category_show_snippet(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(category, ["--sample-file", str(p), "--show", "snippet"])

    assert result.exit_code == 0
    assert "abc" in result.output


def test_category_save_dry_run(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        category, ["--sample-file", str(p), "--save", "snippet-out.txt", "--dry-run"]
    )

    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output


def test_category_debug(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
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

    result = runner.invoke(category, [  # noqa
        "--sample-file", str(sample),
        "--show", "sample"
    ])

    assert result.exit_code == 0
    assert "key: value" in result.output


from click.testing import CliRunner
from pathlib import Path

from textfsmgen.cli.category_cmd import category


def test_category_debug_print_shows_sample_file(tmp_path):
    runner = CliRunner()

    # Create sample sample file
    sample = tmp_path / "sample.txt"
    sample.write_text("alpha: beta\n", encoding="utf-8")

    # Invoke CLI with debug enabled
    result = runner.invoke(
        category,
        [
            "--sample-file", str(sample),
            "--show", "sample",
            "--debug"
        ]
    )

    # Basic success check
    assert result.exit_code == 0

    # Debug output should contain the raw sample text
    assert "sample_file    =" in result.output

    # Debug output should contain a debug marker (adjust to your actual output)
    assert "[DEBUG]" in result.output or "DEBUG" in result.output
