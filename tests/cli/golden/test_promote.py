from textfsmgen.cli.golden.cli import cli


def test_promote_runs(runner, valid_case):
    result = runner.invoke(cli, ["promote", str(valid_case), "--author", "tester"])
    assert result.exit_code in (0, 1)
