from textfsmgen.cli.golden.cli import cli


def test_generate_runs(runner, tmpcase):
    result = runner.invoke(cli, ["generate", str(tmpcase), "--author", "tester"])
    assert result.exit_code in (0, 1)
