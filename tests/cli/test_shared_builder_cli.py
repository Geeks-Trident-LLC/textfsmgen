import json


from textfsmgen.cli.shared_builder_cli import (
    merge,
    validate_config,
    load_sample,
    save_outputs,
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
        "sample_file": "x",
        "command": "",
        "show": "",
        "save": "",
    }
    p = tmpfile("cfg.json", json.dumps(cfg))
    status = validate_config(str(p), list(cfg.keys()), list(cfg["params"].keys()))
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
    result = results[0]
    assert "Invalid save format: " in result["message"]
    assert result["severity"] == "error"
    assert result["kind"] == "parse-expression"



# ------------------------------------------------------------
# show_outputs()
# ------------------------------------------------------------
def test_show_outputs_default(fake_builder):
    result = show_outputs(fake_builder(), "ignored", "")
    assert result
    assert "Value" in str(result)


# ------------------------------------------------------------
# run_builder_workflow()
# ------------------------------------------------------------
def test_run_builder_workflow_success(fake_builder):
    params = {"count": 1, "separator": ":"}
    exit_code = run_builder_workflow(
        builder_class=fake_builder,  # <-- class, not lambda
        sample_file=None,
        cmd="echo hello",
        params=params,
        save="",
        show="snippet",
        config={},
        debug=False,
    )
    assert exit_code == 0
