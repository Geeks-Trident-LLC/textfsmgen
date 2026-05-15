import json

from click.testing import CliRunner
from textfsmgen.cli.top import cli


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def run(args):
    runner = CliRunner()
    return runner.invoke(cli, ["category"] + args)


# ------------------------------------------------------------
# Help behavior
# ------------------------------------------------------------
def test_category_no_options_prints_help():
    result = run([])
    assert result.exit_code == 0
    assert "Category builder" in result.output
    assert "Usage:" in result.output


def test_category_help_flag_h():
    result = run(["-h"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_category_help_flag_help():
    result = run(["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


# ------------------------------------------------------------
# Input-file / command behavior
# ------------------------------------------------------------
def test_category_input_file_prints_value():
    result = run(["--input-file", "sample.txt"])
    assert result.exit_code == 0
    assert "input-file = sample.txt" in result.output


def test_category_command_prints_value():
    result = run(["--command", "echo hi"])
    assert result.exit_code == 0
    assert "command = echo hi" in result.output


def test_category_both_input_and_command_print_values():
    result = run(["--input-file", "x.txt", "--command", "echo hi"])
    assert result.exit_code == 0
    assert "input-file = x.txt" in result.output
    assert "command = echo hi" in result.output


# ------------------------------------------------------------
# Config validation
# ------------------------------------------------------------
def test_category_valid_config(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "params": {
            "count": 1,
            "separator": ":",
            "starting_from": "",
            "ending_at": "",
            "replacing_rules": ""
        },
        "input_file": "x.txt",
        "command": "",
        "show": "",
        "save": ""
    }))

    result = run(["--config", str(cfg)])
    assert result.exit_code == 0
    assert "Config file validated successfully" in result.output


def test_category_invalid_json(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text("{ invalid json }")

    result = run(["--config", str(cfg)])
    # assert result.exit_code == 1
    assert "Failed to load config JSON" in result.output


def test_category_missing_top_level_key(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "params": {},
        "input_file": "",
        "command": "",
        "show": "",
        # missing "save"
    }))

    result = run(["--config", str(cfg)])
    # assert result.exit_code == 1
    assert "Missing required key in config: 'save'" in result.output


def test_category_missing_params_key(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "params": {
            # missing required keys
        },
        "input_file": "x.txt",
        "command": "",
        "show": "",
        "save": ""
    }))

    result = run(["--config", str(cfg)])

    # assert result.exit_code == 1
    assert "Missing required params key" in result.output


def test_category_config_requires_input_or_command(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({
        "params": {
            "count": 1,
            "separator": ":",
            "starting_from": "",
            "ending_at": "",
            "replacing_rules": ""
        },
        "input_file": "",
        "command": "",
        "show": "",
        "save": ""
    }))

    result = run(["--config", str(cfg)])
    # assert result.exit_code == 1
    assert "either 'input_file' or 'command'" in result.output
