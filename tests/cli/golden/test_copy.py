from textfsmgen.cli.golden.cli import cli


def test_copy_creates_case(runner, tmpcase):
    dst = tmpcase.parent / "copy"
    result = runner.invoke(cli, ["copy", str(tmpcase), str(dst), "--author", "tester"])
    assert result.exit_code == 0
    assert dst.exists()
