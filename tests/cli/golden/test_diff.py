from textfsmgen.cli.golden.cli import cli


def test_diff_runs(runner, tmpcase):
    result = runner.invoke(cli, ["diff", str(tmpcase)])
    assert result.exit_code in (0, 1)
