# import json
# import pytest
# from click.testing import CliRunner
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

    result = runner.invoke(category, ["--input-file", str(p), "--show", "snippet"])

    assert result.exit_code == 0
    assert "abc" in result.output


def test_category_save_dry_run(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(
        category, ["--input-file", str(p), "--save", "snippet-out.txt", "--dry-run"]
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
        category, ["--input-file", str(p), "--show", "snippet", "--debug"]
    )

    assert result.exit_code == 0
    assert "[INFO] Loaded sample" in result.output
    assert "=== DEBUG INFO ===" in result.output
