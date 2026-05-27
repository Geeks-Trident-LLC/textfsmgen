from textfsmgen.cli.golden.cli import cli


def test_drift_runs(runner, tmpcase):
    result = runner.invoke(cli, ["drift", str(tmpcase)])
    assert result.exit_code in (0, 1)
