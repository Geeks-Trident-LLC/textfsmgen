from textfsmgen.cli.golden.cli import cli


def test_version(runner):
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "textfsmgen-golden-test" in result.output.lower()

