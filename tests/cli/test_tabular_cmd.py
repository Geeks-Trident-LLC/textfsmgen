import json
import pytest
from click.testing import CliRunner

from textfsmgen.cli.tabular_cmd import tabular
from textfsmgen.libs import file


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample(tmpfile):
    return tmpfile("sample.txt", "fruits meats\n------ -----\norange beef")


@pytest.fixture
def sample1(tmpfile):
    return tmpfile("sample.txt", "apple  pork\norange beef")


@pytest.fixture
def run(runner):
    """Helper to invoke CLI with cleaner syntax."""

    def _run(*args):
        return runner.invoke(tabular, list(args))

    return _run


# -------------------------------------------------------------------
# Tests: Basic behavior
# -------------------------------------------------------------------


def test_help_when_no_input(run):
    result = run()
    assert result.exit_code == 1
    assert "missing required option" in result.output


def test_debug(run, tmpfile, sample):

    result = run(
        "--sample-file",
        sample,
        "--debug",
    )

    assert result.exit_code == 0
    assert f" = {file.path_name(sample)!r}" in result.output


def test_with_headerless_tabular_text(run, tmpfile, sample1):

    result = run(
        "--sample-file",
        sample1,
        "--column-count",
        "2",
        "--headerless",
        "--show",
        "result",
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == [
        {"col0": "apple", "col1": "pork"},
        {"col0": "orange", "col1": "beef"},
    ]


# -------------------------------------------------------------------
# Tests: Config loading
# -------------------------------------------------------------------


def test_load_config(run, sample, tmpfile):
    cfg = {
        "builder": "tabular",
        "params": {
            "column_divider": "",
            "column_count": 0,
            "column_widths": "",
            "headers": None,
            "header_rows": None,
            "custom_header_text": "",
            "starting_from": None,
            "ending_at": None,
            "has_header_row": True,
            "replacing_rules": None,
        },
        "sample_file": file.path_name(sample),
        "command": "",
        "config": "",
        "debug": False,
        "dry_run": False,
        "show": "",
        "save": "",
        "create_config": "",
        "create_golden_test": "",
        "json_mode": False,
    }

    cfg_path = tmpfile("config.cfg", json.dumps(cfg))

    result = run("--config", cfg_path)

    assert result.exit_code == 0
    assert "Value fruits " in result.output
    assert "Value meats " in result.output
    assert "  ^fruits meats" in result.output
    assert "  ^${fruits} +${meats}$$ -> Record" in result.output


def test_invalid_config(run, tmpfile):
    bad_cfg = tmpfile("bad.json", "{}")

    result = run("--config", bad_cfg)
    assert result.exit_code == 1


# -------------------------------------------------------------------
# Tests: Show modes
# -------------------------------------------------------------------


def test_show_sample(run, sample):
    result = run(
        "--sample-file",
        sample,
        "--show",
        "sample",
    )

    assert result.exit_code == 0
    assert "fruits meats" in result.output


def test_show_snippet(run, sample):
    result = run("--sample-file", sample, "--show", "snippet")

    assert result.exit_code == 0
    assert "fruits meats" in result.output
    assert "start() word(var_fruits)  word(var_meats) end() -> record" in result.output


def test_show_template(run, sample):
    result = run(
        "--sample-file",
        sample,
        "--show",
        "template",
    )

    assert result.exit_code == 0
    assert "Value fruits " in result.output
    assert "Value meats " in result.output
    assert "  ^fruits meats" in result.output
    assert "  ^${fruits} +${meats}$$ -> Record" in result.output


def test_show_result(run, sample):
    result = run(
        "--sample-file",
        sample,
        "--show",
        "result",
    )

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data == [{"fruits": "orange", "meats": "beef"}]


# -------------------------------------------------------------------
# Tests: Save (dry-run)
# -------------------------------------------------------------------


def test_save_sample_with_dryrun(run, sample):
    out_file = sample.parent / "out.txt"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"sample-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] sample " in result.output
    assert file.path_name(out_file) in result.output


def test_save_snippet_with_dryrun(run, sample):
    out_file = sample.parent / "snippet.txt"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"snippet-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] snippet " in result.output
    assert file.path_name(out_file) in result.output


def test_save_template_with_dryrun(run, sample):
    out_file = sample.parent / "textfsm.template"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"template-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] template " in result.output
    assert file.path_name(out_file) in result.output


def test_save_result_with_dryrun(run, sample):
    out_file = sample.parent / "result.json"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"result-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] result " in result.output
    assert file.path_name(out_file) in result.output


# -------------------------------------------------------------------
# Tests: Save (real)
# -------------------------------------------------------------------


def test_save_sample(run, sample):
    out_file = sample.parent / "out.txt"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"sample-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved sample " in result.output
    assert out_file.exists()


def test_save_snippet(run, sample):
    out_file = sample.parent / "snippet.txt"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"snippet-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved snippet " in result.output
    assert out_file.exists()


def test_save_template(run, sample):
    out_file = sample.parent / "textfsm.template"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"template-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved template " in result.output
    assert out_file.exists()


def test_save_result(run, sample):
    out_file = sample.parent / "result.json"

    result = run(
        "--sample-file",
        sample,
        "--save",
        f"result-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved result " in result.output
    assert out_file.exists()


# -------------------------------------------------------------------
# Tests: Create config
# -------------------------------------------------------------------


def test_create_config_with_dryrun(run, sample):
    cfg_path = sample.parent / "config.cfg"

    result = run(
        "--sample-file",
        file.path_name(sample),
        "--create-config",
        file.path_name(cfg_path),
        "--dry-run",
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["sample_file"] == file.path_name(sample)


def test_create_config(run, sample):
    cfg_path = sample.parent / "config.cfg"

    result = run(
        "--sample-file",
        file.path_name(sample),
        "--create-config",
        file.path_name(cfg_path),
    )
    assert result.exit_code == 0
    assert f"Config file {file.path_name(cfg_path)!r} created!" in result.output

    data = json.loads(cfg_path.read_text())
    assert data["sample_file"] == file.path_name(sample)


# -------------------------------------------------------------------
# Tests: Golden tests
# -------------------------------------------------------------------


def test_create_golden_test_with_dryrun(run, sample):
    case_path = sample.parent / "tests" / "golden" / "integration" / "case1"

    result = run(
        "--sample-file",
        sample,
        "--create-golden-test",
        case_path,
        "--dry-run",
    )

    assert result.exit_code == 0
    out = result.output

    assert "[DRY-RUN]" in out
    assert file.path_name(case_path / "inputs" / "sample.txt") in out
    assert file.path_name(case_path / "expected" / "snippet.txt") in out
    assert file.path_name(case_path / "expected" / "textfsm.template") in out
    assert file.path_name(case_path / "expected_results" / "sample_result.json") in out
    assert file.path_name(case_path / "manifest.json") in out


def test_create_golden_test(run, sample):
    case_path = sample.parent / "tests" / "golden" / "integration" / "case1"

    result = run(
        "--sample-file",
        sample,
        "--create-golden-test",
        case_path,
    )

    assert result.exit_code == 0
    assert f"Golden test created at {file.path_name(case_path)!r}" in result.output

    assert (case_path / "inputs" / "sample.txt").exists()
    assert (case_path / "expected" / "snippet.txt").exists()
    assert (case_path / "expected" / "textfsm.template").exists()
    assert (case_path / "expected_results" / "sample_result.json").exists()
    assert (case_path / "manifest.json").exists()
