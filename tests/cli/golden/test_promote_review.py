from textfsmgen.cli.golden.cli import cli


def test_promote_review_runs(runner, tmpcase):
    result = runner.invoke(cli, ["promote-review", str(tmpcase)])
    assert result.exit_code in (0, 1)
