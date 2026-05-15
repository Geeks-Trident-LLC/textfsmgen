import json
import pytest
# from click.testing import CliRunner
# from pathlib import Path

from textfsmgen.cli.category_cmd import (
    validate_config,
    merge,
    load_sample_from_input_or_cmd,
    save_outputs,
    dry_run_save,
    show_outputs,
    category,
)

# from textfsmgen.libs.generic import StatusString


# ------------------------------------------------------------
# merge()
# ------------------------------------------------------------
def test_merge_cli_overrides_config():
    assert merge("cli", {"key": "cfg"}, "key", "default") == "cli"


def test_merge_config_used_when_cli_empty():
    assert merge("", {"key": "cfg"}, "key", "default") == "cfg"


def test_merge_default_used_when_missing():
    assert merge("", {}, "key", "default") == "default"


# ------------------------------------------------------------
# validate_config()
# ------------------------------------------------------------
def test_validate_config_valid(tmpfile):
    cfg = {
        "params": {
            "count": 1,
            "separator": ":",
            "starting_from": "",
            "ending_at": "",
            "replacing_rules": "",
        },
        "input_file": "x",
        "command": "",
        "show": "",
        "save": "",
    }
    p = tmpfile("cfg.json", json.dumps(cfg))
    status = validate_config(str(p))
    assert status
    assert status.raw == cfg


@pytest.mark.parametrize("bad", [
    {},  # missing everything
    {"params": {}},  # missing top-level keys
])
def test_validate_config_missing_top(tmpfile, bad):
    p = tmpfile("cfg.json", json.dumps(bad))
    status = validate_config(str(p))
    assert not status
    assert status.reason == "warning"


def test_validate_config_missing_params(tmpfile):
    cfg = {
        "params": {"count": 1},
        "input_file": "x",
        "command": "",
        "show": "",
        "save": "",
    }
    p = tmpfile("cfg.json", json.dumps(cfg))
    status = validate_config(str(p))
    assert not status
    assert status.reason == "warning"


def test_validate_config_invalid_json(tmpfile):
    p = tmpfile("cfg.json", "{not json")
    status = validate_config(str(p))
    assert not status
    assert status.reason == "error"


# ------------------------------------------------------------
# load_sample_from_input_or_cmd()
# ------------------------------------------------------------
def test_load_sample_from_file_success(tmpfile):
    p = tmpfile("sample.txt", "hello")
    status = load_sample_from_input_or_cmd(str(p), "")
    assert status
    assert status == "hello"


def test_load_sample_from_file_empty(tmpfile):
    p = tmpfile("sample.txt", "")
    status = load_sample_from_input_or_cmd(str(p), "")
    assert not status
    assert status.reason == "warning"


def test_load_sample_from_file_error(tmp_path):
    p = tmp_path / "missing.txt"
    status = load_sample_from_input_or_cmd(str(p), "")
    assert not status
    assert status.reason == "error"


def test_load_sample_from_cmd_success(monkeypatch):
    class FakeResult:
        is_success = True
        output = "cmd output"

    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.shell.execute_command",
        lambda c: FakeResult(),
    )

    status = load_sample_from_input_or_cmd("", "cmd")
    assert status
    assert status == "cmd output"


def test_load_sample_from_cmd_empty(monkeypatch):
    class FakeResult:
        is_success = True
        output = ""

    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.shell.execute_command",
        lambda c: FakeResult(),
    )

    status = load_sample_from_input_or_cmd("", "cmd")
    assert not status
    assert status.reason == "warning"


def test_load_sample_from_cmd_error(monkeypatch):
    class FakeResult:
        is_success = False
        output = "err"

    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.shell.execute_command",
        lambda c: FakeResult(),
    )

    status = load_sample_from_input_or_cmd("", "cmd")
    assert not status
    assert status.reason == "error"


# ------------------------------------------------------------
# save_outputs()
# ------------------------------------------------------------
def test_save_outputs_snippet(tmpfile, monkeypatch, fake_builder):
    b = fake_builder()
    sample = "ignored"

    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.Path.write_text",
        lambda self, content, encoding="utf-8": None,
    )

    results = save_outputs(b, sample, "snippet-out.txt")
    assert len(results) == 1
    assert results[0]


def test_save_outputs_invalid_format(fake_builder):
    results = save_outputs(fake_builder(), "sample", "badformat")
    assert len(results) == 1
    assert not results[0]


def test_save_outputs_unknown_type(fake_builder):
    results = save_outputs(fake_builder(), "sample", "weird-out.txt")
    assert not results[0]


# ------------------------------------------------------------
# dry_run_save()
# ------------------------------------------------------------
def test_dry_run_save_valid(fake_builder):
    b = fake_builder()
    sample = "ignored"

    results = dry_run_save(b, sample, "snippet-out.txt")
    assert results[0]
    assert "[DRY-RUN]" in results[0]


def test_dry_run_save_invalid(fake_builder):
    results = dry_run_save(fake_builder(), "sample", "badformat")
    assert not results[0]
    assert "[DRY-RUN]" in results[0]


# ------------------------------------------------------------
# show_outputs()
# ------------------------------------------------------------
def test_show_outputs_default(fake_builder):
    b = fake_builder()
    sample = "ignored"
    status = show_outputs(b, sample, "")
    assert status
    assert "Value" in status


def test_show_outputs_json(fake_builder):
    b = fake_builder()
    sample = "ignored"
    status = show_outputs(b, sample, "json(snippet)")
    assert status
    data = json.loads(status)
    assert "snippet" in data


def test_show_outputs_sample(fake_builder):
    b = fake_builder()
    sample = "hello"
    status = show_outputs(b, sample, "sample")
    assert status
    assert "hello" in status


# ------------------------------------------------------------
# CLI: category
# ------------------------------------------------------------
def test_category_cli_help(runner):
    result = runner.invoke(category, [])
    assert result.exit_code == 0
    assert "Category builder" in result.output


def test_category_cli_show_snippet(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(category, [
        "--input-file", str(p),
        "--show", "snippet"
    ])

    assert result.exit_code == 0
    assert "abc" in result.output


def test_category_cli_save_dry_run(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(category, [
        "--input-file", str(p),
        "--save=snippet-out.txt",
        "--dry-run"
    ])

    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output


def test_category_cli_debug(tmpfile, runner, monkeypatch, fake_builder):
    monkeypatch.setattr(
        "textfsmgen.cli.category_cmd.CategoryTemplateBuilder",
        lambda user_data, **params: fake_builder(user_data, **params),
    )

    p = tmpfile("sample.txt", "hello")

    result = runner.invoke(category, [
        "--input-file", str(p),
        "--show", "snippet",
        "--debug"
    ])

    assert result.exit_code == 0
    assert "[INFO] Loaded sample" in result.output
    assert "=== DEBUG INFO ===" in result.output
