import json
import pytest
from click.testing import CliRunner

from textfsmgen.cli.freeform_cmd import freeform
from textfsmgen.libs import file


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def snippet():
    return "word(var_v0)"


@pytest.fixture
def sample(tmpfile):
    return tmpfile("sample.txt", "hello")


@pytest.fixture
def run(runner):
    """Helper to invoke CLI with cleaner syntax."""

    def _run(*args):
        return runner.invoke(freeform, list(args))

    return _run


# -------------------------------------------------------------------
# Tests: Basic behavior
# -------------------------------------------------------------------


def test_help_when_no_input(run):
    result = run()
    assert result.exit_code == 1
    assert "missing required option" in result.output


def test_debug(run, tmpfile, snippet):
    snippet_path = tmpfile("user-snippet.txt", "abc word(var_v0)")

    result = run(
        "--snippet-file",
        file.path_name(snippet_path),
        "--snippet",
        snippet,
        "--debug",
    )

    assert result.exit_code == 0
    assert f" = {file.path_name(snippet_path)!r}" in result.output


# -------------------------------------------------------------------
# Tests: Config loading
# -------------------------------------------------------------------


def test_load_config(run, tmpfile):
    cfg = {
        "builder": "freeform",
        "params": {},
        "snippet": "word(var_v0)",
        "snippet_file": "",
        "sample_file": "",
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
    assert " v0 " in result.output


def test_invalid_config(run, tmpfile):
    bad_cfg = tmpfile("bad.json", "{}")

    result = run("--config", bad_cfg)
    assert result.exit_code == 1


# -------------------------------------------------------------------
# Tests: Show modes
# -------------------------------------------------------------------


def test_show_sample(run, sample, snippet):
    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--show",
        "sample",
    )

    assert result.exit_code == 0
    assert "hello" in result.output


def test_show_snippet(run, snippet):
    result = run("--snippet", snippet, "--show", "snippet")

    assert result.exit_code == 0
    assert snippet in result.output


def test_show_template(run, sample, snippet):
    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--show",
        "template",
    )

    assert result.exit_code == 0
    assert "Value v0 " in result.output
    assert "Start" in result.output


def test_show_result(run, sample, snippet):
    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--show",
        "result",
    )

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data[0]["v0"] == "hello"


# -------------------------------------------------------------------
# Tests: Save (dry-run)
# -------------------------------------------------------------------


def test_save_sample_with_dryrun(run, sample, snippet):
    out_file = sample.parent / "out.txt"

    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--save",
        f"sample-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] sample " in result.output
    assert file.path_name(out_file) in result.output


def test_save_snippet_with_dryrun(run, sample, snippet):
    out_file = sample.parent / "snippet.txt"

    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--save",
        f"snippet-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] snippet " in result.output
    assert file.path_name(out_file) in result.output


def test_save_template_with_dryrun(run, sample, snippet):
    out_file = sample.parent / "textfsm.template"

    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--save",
        f"template-{file.path_name(out_file)}",
        "--dry-run",
    )

    assert result.exit_code == 0
    assert "[DRY-RUN] template " in result.output
    assert file.path_name(out_file) in result.output


def test_save_result_with_dryrun(run, sample, snippet):
    out_file = sample.parent / "result.json"

    result = run(
        "--snippet",
        snippet,
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


def test_save_sample(run, sample, snippet):
    out_file = sample.parent / "out.txt"

    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--save",
        f"sample-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved sample " in result.output
    assert out_file.exists()


def test_save_snippet(run, sample, snippet):
    out_file = sample.parent / "snippet.txt"

    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--save",
        f"snippet-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved snippet " in result.output
    assert out_file.exists()


def test_save_template(run, sample, snippet):
    out_file = sample.parent / "textfsm.template"

    result = run(
        "--snippet",
        snippet,
        "--sample-file",
        sample,
        "--save",
        f"template-{out_file}",
    )

    assert result.exit_code == 0
    assert "Saved template " in result.output
    assert out_file.exists()


def test_save_result(run, sample, snippet):
    out_file = sample.parent / "result.json"

    result = run(
        "--snippet",
        snippet,
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


def test_create_config_with_dryrun(run, sample, snippet):
    cfg_path = sample.parent / "config.cfg"

    result = run(
        "--sample-file",
        file.path_name(sample),
        "--snippet",
        snippet,
        "--create-config",
        file.path_name(cfg_path),
        "--dry-run",
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["snippet"] == snippet
    assert data["sample_file"] == file.path_name(sample)


def test_create_config(run, sample, snippet):
    cfg_path = sample.parent / "config.cfg"

    result = run(
        "--sample-file",
        file.path_name(sample),
        "--snippet",
        snippet,
        "--create-config",
        file.path_name(cfg_path),
    )
    assert result.exit_code == 0
    assert f"Config file {file.path_name(cfg_path)!r} created!" in result.output

    data = json.loads(cfg_path.read_text())
    assert data["snippet"] == snippet
    assert data["sample_file"] == file.path_name(sample)


# -------------------------------------------------------------------
# Tests: Golden tests
# -------------------------------------------------------------------


def test_create_golden_test_with_dryrun(run, sample, snippet):
    case_path = sample.parent / "tests" / "golden" / "integration" / "case1"

    result = run(
        "--sample-file",
        sample,
        "--snippet",
        snippet,
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


def test_create_golden_test(run, sample, snippet):
    case_path = sample.parent / "tests" / "golden" / "integration" / "case1"

    result = run(
        "--sample-file",
        sample,
        "--snippet",
        snippet,
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
