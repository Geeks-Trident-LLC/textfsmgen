import pytest
from click.testing import CliRunner
from unittest.mock import patch

from textfsmgen.cli.golden.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def patch_cmd(cmd_name: str):
    """
    Patch the function actually called by the Click command.
    """
    mapping = {
        "run": "run",
        "regen": "regen",
        "diff": "diff",
        "drift": "drift",
        "quicktest": "quicktest",
        "copy": "copy_case",
        "duplicate": "duplicate_case",
        "new": "new",
        "new_from_input": "new_from_input",
        "generate": "generate",
        "batch_generate": "batch_generate",
        "batch_regen": "batch_regen",
        "batch_quicktest": "batch_quicktest",
        "merge": "merge",
        "merge_review": "merge_review",
        "merge_preview": "merge_preview",
        "merge_diff": "merge_diff",
        "identical": "run_identical",
    }

    func = mapping[cmd_name]
    return patch(f"textfsmgen.cli.golden.cli.cmd_{cmd_name}.{func}")


@pytest.mark.parametrize(
    "argv, cmd_name",
    [
        (["run", "--dry-run", "case-dir"], "run"),
        (["regen", "--dry-run", "case-dir"], "regen"),
        (["diff", "case-dir"], "diff"),
        (["drift", "case-dir"], "drift"),
        (["quicktest", "--dry-run", "case-dir"], "quicktest"),
        (["copy", "--dry-run", "--force", "me", "src", "dst"], "copy"),
        (["duplicate", "--dry-run", "--force", "me", "src"], "duplicate"),
        (["new", "case-dir"], "new"),
        (
            [
                "new-from-input",
                "--builder",
                "mybuilder",
                "--author",
                "me",
                "case-dir",
                "inputs-dir",
            ],
            "new_from_input",
        ),
        pytest.param(
            ["generate", "case-dir"],
            "generate",
            marks=pytest.mark.skip(reason="generate command not ready yet"),
        ),
        (["batch-generate", "root-dir"], "batch_generate"),
        (["batch-regen", "root-dir"], "batch_regen"),
        (["batch-quicktest", "root-dir"], "batch_quicktest"),
        (["merge", "--author", "me", "dst", "src-a", "src-b"], "merge"),
        (["merge-review", "dst", "src-a", "src-b"], "merge_review"),
        (["merge-preview", "src-a", "src-b"], "merge_preview"),
        (["merge-diff", "src-a", "src-b"], "merge_diff"),
        (["identical", "src-a", "src-b"], "identical"),
    ],
)
def test_subcommand_invokes_correct_target(runner, argv, cmd_name):
    with patch_cmd(cmd_name) as mock_cmd:
        mock_cmd.return_value = 0

        result = runner.invoke(cli, argv)

        assert result.exit_code == 0, result.output
        mock_cmd.assert_called_once()


def test_run_parsing_with_dry_run_and_case(runner):
    with patch_cmd("run") as mock_run:
        mock_run.return_value = 0

        result = runner.invoke(cli, ["run", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        # first arg is Path(case)
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_regen_parsing_with_dry_run(runner):
    with patch_cmd("regen") as mock_regen:
        mock_regen.return_value = 0

        result = runner.invoke(cli, ["regen", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_regen.assert_called_once()
        args, kwargs = mock_regen.call_args
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_quicktest_parsing_with_dry_run(runner):
    with patch_cmd("quicktest") as mock_qt:
        mock_qt.return_value = 0

        result = runner.invoke(cli, ["quicktest", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_qt.assert_called_once()
        args, kwargs = mock_qt.call_args
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_copy_parsing_flags(runner):
    with patch_cmd("copy") as mock_copy:
        mock_copy.return_value = 0

        result = runner.invoke(
            cli,
            ["copy", "--dry-run", "--force", "me", "src-dir", "dst-dir"],
        )

        assert result.exit_code == 0
        mock_copy.assert_called_once()
        args, kwargs = mock_copy.call_args

        assert kwargs["author"] == "me"
        assert str(kwargs["src"]).endswith("src-dir")
        assert str(kwargs["dst"]).endswith("dst-dir")
        assert kwargs["dry_run"] is True
        assert kwargs["force"] is True


def test_new_from_input_required_flags(runner):
    with patch_cmd("new_from_input") as mock_new_in:
        mock_new_in.return_value = 0

        result = runner.invoke(
            cli,
            [
                "new-from-input",
                "--builder",
                "mybuilder",
                "--author",
                "me",
                "case-dir",
                "inputs-dir",
            ],
        )

        assert result.exit_code == 0
        mock_new_in.assert_called_once()
        args, kwargs = mock_new_in.call_args

        case_path, inputs_dir = args[0], args[1]
        assert str(case_path).endswith("case-dir")
        assert str(inputs_dir).endswith("inputs-dir")
        assert kwargs["builder"] == "mybuilder"
        assert kwargs["author"] == "me"
        # params default "{}"
        assert kwargs["params"] == {}


def test_merge_preview_compact_and_json(runner):
    with patch_cmd("merge_preview") as mock_mp:
        mock_mp.return_value = 0

        result = runner.invoke(
            cli,
            ["merge-preview", "--compact", "--json", "src-a", "src-b"],
        )

        assert result.exit_code == 0
        mock_mp.assert_called_once()
        args, kwargs = mock_mp.call_args

        srcs = args[0]
        assert [str(p) for p in srcs] == ["src-a", "src-b"]
        assert kwargs["compact"] is True
        assert kwargs["is_json"] is True


def test_merge_diff_flags(runner):
    with patch_cmd("merge_diff") as mock_md:
        mock_md.return_value = 0

        result = runner.invoke(
            cli,
            [
                "merge-diff",
                "--compact",
                "--json",
                "--diff-count",
                "5",
                "--diff-names-only",
                "src-a",
                "src-b",
            ],
        )

        assert result.exit_code == 0
        mock_md.assert_called_once()
        args, kwargs = mock_md.call_args

        srcs = args[0]
        assert [str(p) for p in srcs] == ["src-a", "src-b"]
        assert kwargs["compact"] is True
        assert kwargs["is_json"] is True
        assert kwargs["diff_count"] == 5
        assert kwargs["diff_names_only"] is True


def test_identical_modes(runner):
    with patch_cmd("identical") as mock_ident:
        mock_ident.return_value = 0

        result = runner.invoke(
            cli,
            ["identical", "--compact", "--json", "src-a", "src-b"],
        )

        assert result.exit_code == 0
        mock_ident.assert_called_once()
        args, kwargs = mock_ident.call_args

        srcs = args[0]
        assert [str(p) for p in srcs] == ["src-a", "src-b"]
        assert kwargs["compact"] is True
        assert kwargs["is_json"] is True
