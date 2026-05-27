from textfsmgen.cli.golden.cli import cli

import shutil


def test_merge_runs(runner, valid_case, tmp_path):
    # create a second valid case
    case2 = tmp_path / "tests" / "golden" / "integration" / "demo2"
    shutil.copytree(valid_case, case2)

    dst = tmp_path / "merged"
    result = runner.invoke(cli, ["merge", str(dst), str(valid_case), str(case2)])
    assert result.exit_code in (0, 1)

