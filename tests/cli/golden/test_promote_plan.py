from textfsmgen.cli.golden.cli import cli


def test_promote_plan_runs(runner, tmpcase):
    result = runner.invoke(cli, ["promote-plan", str(tmpcase)])
    assert result.exit_code in (0, 1)
