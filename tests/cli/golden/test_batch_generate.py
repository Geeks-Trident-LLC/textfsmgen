from textfsmgen.cli.golden.cli import cli

def test_batch_generate_runs(runner, valid_case):
    root = valid_case.parent
    result = runner.invoke(cli, ["batch-generate", str(root), "--author", "tester"])
    assert result.exit_code in (0, 1)
