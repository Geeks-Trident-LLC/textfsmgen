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
    assert "Invalid save item " in result["message"]
    assert result["severity"] == "error"
    assert result["kind"] == "parse-expression"


def test_save_outputs_sample_always_allowed(fake_builder, tmp_path):
    filename = tmp_path / "out.txt"
    spec = f"sample-{filename}"

    results = save_outputs(fake_builder(), "hello", spec)
    result = results[0]

    assert result["kind"] == "sample"
    assert result["path"] == str(filename)
    assert result["severity"] == "info"
    assert "Saved sample →" in result["message"]

    # file should exist
    assert filename.read_text() == "hello"


def test_save_outputs_missing_snippet(fake_builder, tmp_path):
    filename = tmp_path / "snippet.txt"
    spec = f"snippet-{filename}"

    builder = fake_builder()
    builder.snippet = None  # ensure missing

    results = save_outputs(builder, "sample", spec)
    result = results[0]

    assert result["kind"] == "snippet"
    assert result["severity"] == "warning"
    assert "Builder has no 'snippet' content" in result["message"]


def test_save_outputs_builder_warning_blocks(fake_builder, tmp_path):
    filename = tmp_path / "out.json"
    spec = f"result-{filename}"

    builder = fake_builder()
    builder.warning = "bad template"

    results = save_outputs(builder, "sample", spec)
    result = results[0]

    assert result["kind"] == "build-result"
    assert result["severity"] == "error"
    assert "Cannot proceed" in result["message"]


def test_save_outputs_dryrun(fake_builder, tmp_path):
    filename = tmp_path / "out.txt"
    spec = f"dryrun(sample-{filename})"

    results = save_outputs(fake_builder(), "hello", spec)
    result = results[0]

    assert result["kind"] == "sample"
    assert result["severity"] == "info"
    assert "[DRY-RUN]" in result["message"]
    assert "sample →" in result["message"]

    # file should NOT exist
    assert not filename.exists()


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
