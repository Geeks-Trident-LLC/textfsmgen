from textfsmgen.cli.golden.cli import cli


def test_merge_diff_runs(runner, tmp_path):
    root = tmp_path / "tests" / "golden" / "integration"
    root.mkdir(parents=True)
    (root / "a").mkdir()

    result = runner.invoke(cli, ["merge-diff", str(root / "a")])
    assert result.exit_code in (0, 1)
