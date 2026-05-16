import json
import copy
import pytest
from click.testing import CliRunner

from textfsmgen.cli.config_cmd import config, CONFIG_TYPES


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def write_temp_json(tmp_path, data, name="cfg.json"):
    p = tmp_path / name
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


# ------------------------------------------------------------
# config list
# ------------------------------------------------------------
def test_config_list():
    runner = CliRunner()
    result = runner.invoke(config, ["list"])

    assert result.exit_code == 0
    for name in CONFIG_TYPES.keys():
        assert f"- {name}" in result.output


# ------------------------------------------------------------
# config create
# ------------------------------------------------------------
@pytest.mark.parametrize("cfg_type", ["category", "tabular"])
def test_config_create_stdout(cfg_type):
    runner = CliRunner()
    result = runner.invoke(config, ["create", cfg_type])

    assert result.exit_code == 0
    loaded = json.loads(result.output)
    assert loaded == CONFIG_TYPES[cfg_type]


@pytest.mark.parametrize("cfg_type", ["category", "tabular"])
def test_config_create_output_file(tmp_path, cfg_type):
    runner = CliRunner()
    outfile = tmp_path / f"{cfg_type}.json"

    result = runner.invoke(config, ["create", cfg_type, "--output", str(outfile)])
    assert result.exit_code == 0
    assert outfile.exists()

    loaded = json.loads(outfile.read_text(encoding="utf-8"))
    assert loaded == CONFIG_TYPES[cfg_type]


# ------------------------------------------------------------
# config validate
# ------------------------------------------------------------
@pytest.mark.parametrize("cfg_type", ["category", "tabular"])
def test_config_validate_success(tmp_path, cfg_type):
    cfg = copy.deepcopy(CONFIG_TYPES[cfg_type])
    p = write_temp_json(tmp_path, cfg)

    runner = CliRunner()
    result = runner.invoke(config, ["validate", str(p)])

    assert result.exit_code == 0
    assert "is valid" in result.output


def test_config_validate_missing_top_level(tmp_path):
    bad = copy.deepcopy(CONFIG_TYPES["category"])
    bad.pop("show")

    p = write_temp_json(tmp_path, bad, name="missing_show.json")

    runner = CliRunner()
    result = runner.invoke(config, ["validate", str(p)])

    assert result.exit_code == 1
