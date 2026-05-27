from textfsmgen.cli.golden.cli import cli


def test_duplicate_creates_case(runner, valid_case):
    result = runner.invoke(cli, [
        "duplicate",
        str(valid_case),
        "--author", "tester"
    ])

    assert result.exit_code in (0, 1)

    parent = valid_case.parent
    copies = [p for p in parent.iterdir() if p.name.startswith("demo-copy")]
    assert copies
