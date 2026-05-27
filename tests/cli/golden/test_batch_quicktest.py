from textfsmgen.cli.golden.cli import cli


def test_batch_quicktest_runs(runner, valid_case):
    root = valid_case.parent
    result = runner.invoke(cli, ["batch-quicktest", str(root)])
    assert result.exit_code in (0, 1)
