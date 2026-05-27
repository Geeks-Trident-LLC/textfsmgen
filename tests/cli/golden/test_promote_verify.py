from textfsmgen.cli.golden.cli import cli
import json
import shutil


def test_promote_verify_json(runner, valid_case, tmp_path):
    # convert integration → main
    main = tmp_path / "tests" / "golden" / "main" / "demo"
    main.mkdir(parents=True)
    shutil.copytree(valid_case, main, dirs_exist_ok=True)

    result = runner.invoke(cli, ["promote-verify", "--json", str(main)])
    assert result.exit_code in (0, 1)

    data = json.loads(result.output)
    assert "events" in data

