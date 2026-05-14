from click.testing import CliRunner
from unittest.mock import patch

# IMPORTANT:
# Update this import if your top-level CLI file is in a different module.
from textfsmgen.cli.top import cli


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "textfsmgen" in result.output
    assert "." in result.output  # version number present


def test_help_shows_commands():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "tester" in result.output
    assert "--version" in result.output


def test_no_arguments_shows_help():
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_tester_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["tester", "--help"])
    assert result.exit_code == 0
    assert "Golden" in result.output
    assert "utilities" in result.output


def test_tester_forwards_arguments():
    runner = CliRunner()

    with patch("textfsmgen.cli.top.TesterCLI") as MockTester:
        instance = MockTester.return_value
        instance.run_from_argv.return_value = 0

        result = runner.invoke(cli, ["tester", "run", "demo"])

        assert result.exit_code == 0
        instance.run_from_argv.assert_called_once_with(["run", "demo"])


def test_tester_no_args_forwards_empty_list():
    runner = CliRunner()

    with patch("textfsmgen.cli.top.TesterCLI") as MockTester:
        instance = MockTester.return_value
        instance.run_from_argv.return_value = 0

        result = runner.invoke(cli, ["tester"])

        assert result.exit_code == 0
        instance.run_from_argv.assert_called_once_with([])


def test_unknown_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["unknown"])
    assert result.exit_code != 0
    assert "No such command" in result.output
