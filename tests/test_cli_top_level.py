import argparse
from types import SimpleNamespace

import pytest

from textfsmgen.cli import Cli


@pytest.fixture
def cli():
    return Cli()


@pytest.fixture
def parser(cli) -> argparse.ArgumentParser:
    return cli._build_parser()


def test_parser_has_tester_subcommand(parser):
    # Ensure "tester" subparser is registered
    args = parser.parse_args(["tester"])
    assert args.command == "tester"
    assert hasattr(args, "func")
    # Bound to the correct dispatcher
    assert args.func.__name__ == "_dispatch_tester"


def test_tester_remainder_captures_all_args(parser):
    # Everything after "tester" should go into args.remaining
    args = parser.parse_args(["tester", "run", "tests/main/demo", "--dry-run"])
    assert args.command == "tester"
    assert args.remaining == ["run", "tests/main/demo", "--dry-run"]


def test_run_without_subcommand_prints_help_and_returns_nonzero(cli, capsys, monkeypatch):
    # Simulate running: textfsmgen
    monkeypatch.setattr("sys.argv", ["textfsmgen"])

    exit_code = cli.run()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "usage: textfsmgen" in captured.out


def test_dispatch_tester_forwards_to_testercli(monkeypatch):
    calls = []

    class FakeTesterCLI:
        def run_from_argv(self, argv):
            calls.append(list(argv))
            return 42

    # Patch TesterCLI used inside Cli._dispatch_tester
    from textfsmgen import cli as cli_module

    monkeypatch.setattr(cli_module, "TesterCLI", FakeTesterCLI)

    args = SimpleNamespace(remaining=["run", "tests/main/demo"])
    exit_code = Cli._dispatch_tester(args)

    assert exit_code == 42
    assert calls == [["run", "tests/main/demo"]]
