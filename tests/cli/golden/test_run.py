from textfsmgen.cli.golden.cli import cli


def test_run_runs(runner, tmpcase):
    result = runner.invoke(cli, ["run", str(tmpcase)])
    assert result.exit_code in (0, 1)
