from textfsmgen.cli.golden.cli import cli


def test_new_creates_case(runner, tmp_path):
    dst = tmp_path / "tests" / "golden" / "integration" / "newcase"
    result = runner.invoke(cli, ["new", str(dst), "--builder", "category", "--author", "tester"])
    assert result.exit_code == 0
    assert dst.exists()
