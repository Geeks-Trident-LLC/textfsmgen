import json
from pathlib import Path

from click.testing import CliRunner

from textfsmgen.cli.shared_builder_cli import (
    merge,
    validate_config,
    load_sample,
    save_outputs,
    dry_run_save,
    show_outputs,
    run_builder_workflow,
)


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
    status = validate_config(str(p), list(cfg["params"].keys()))
    assert status
    assert status.raw == cfg


# ------------------------------------------------------------
# load_sample()
# ------------------------------------------------------------
def test_load_sample_from_file_success(tmpfile):
    p = tmpfile("sample.txt", "hello")
    status = load_sample(str(p), "")
    assert status
    assert status == "hello"


# ------------------------------------------------------------
# save_outputs()
# ------------------------------------------------------------
def test_save_outputs_invalid_format(fake_builder):
    results = save_outputs(fake_builder(), "sample", "badformat")
    assert not results[0]


# ------------------------------------------------------------
# dry_run_save()
# ------------------------------------------------------------
def test_dry_run_save_valid(fake_builder):
    results = dry_run_save(fake_builder(), "sample", "snippet-out.txt")
    assert results[0]
    assert "[DRY-RUN]" in results[0]


# ------------------------------------------------------------
# show_outputs()
# ------------------------------------------------------------
def test_show_outputs_default(fake_builder):
    status = show_outputs(fake_builder(), "ignored", "")
    assert status
    assert "Value" in status


# ------------------------------------------------------------
# run_builder_workflow()
# ------------------------------------------------------------
def test_run_builder_workflow_success(fake_builder):
    params = {"count": 1, "separator": ":"}
    exit_code = run_builder_workflow(
        builder_class=lambda user_data, **p: fake_builder(user_data, **p),
        input_file=None,
        cmd="echo hello",
        params=params,
        save="",
        show="snippet",
        config={},
        debug=False,
        dry_run=False,
    )
    assert exit_code == 0
