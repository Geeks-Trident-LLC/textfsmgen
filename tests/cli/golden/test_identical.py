from textfsmgen.cli.golden.cli import cli


def test_identical_runs(runner, tmp_path):
    root = tmp_path / "tests" / "golden" / "integration"
    root.mkdir(parents=True)
    (root / "a").mkdir()

    result = runner.invoke(cli, ["identical", str(root)])
    assert result.exit_code == 0
