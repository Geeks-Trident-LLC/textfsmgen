from textfsmgen.cli.golden.cli import cli
import json


def test_promote_diff_json(runner, valid_case):
    result = runner.invoke(cli, ["promote-diff", "--json", str(valid_case)])
    assert result.exit_code in (0, 1)

    data = json.loads(result.output)
    assert "events" in data
