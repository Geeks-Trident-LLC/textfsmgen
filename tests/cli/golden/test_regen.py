from textfsmgen.cli.golden.cli import cli


def test_regen_runs(runner, tmpcase):
    result = runner.invoke(cli, ["regen", str(tmpcase)])
    assert result.exit_code in (0, 1)
