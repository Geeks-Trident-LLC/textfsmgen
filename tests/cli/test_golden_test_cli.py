import pytest
from click.testing import CliRunner
from unittest.mock import patch

from textfsmgen.tester.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.mark.parametrize(
    "argv, target_path, target_name",
    [
        (["run", "--dry-run", "case-dir"], "textfsmgen.tester.cli.cmd_run.run", "run"),
        (
            ["regen", "--dry-run", "case-dir"],
            "textfsmgen.tester.cli.cmd_regen.regen",
            "regen",
        ),
        (["diff", "case-dir"], "textfsmgen.tester.cli.cmd_diff.diff", "diff"),
        (["drift", "case-dir"], "textfsmgen.tester.cli.cmd_drift.drift", "drift"),
        (
            ["quicktest", "--dry-run", "case-dir"],
            "textfsmgen.tester.cli.cmd_quicktest.quicktest",
            "quicktest",
        ),
        (
            ["copy", "--dry-run", "--force", "me", "src-dir", "dst-dir"],
            "textfsmgen.tester.cli.cmd_copy.copy_case",
            "copy",
        ),
        (
            ["duplicate", "--dry-run", "--force", "me", "src-dir"],
            "textfsmgen.tester.cli.cmd_duplicate.duplicate_case",
            "duplicate",
        ),
        (["new", "case-dir"], "textfsmgen.tester.cli.cmd_new.new", "new"),
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
            "textfsmgen.tester.cli.cmd_new_from_input.new_from_input",
            "new-from-input",
        ),
        pytest.param(
            ["generate", "case-dir"],
            "textfsmgen.tester.cli.cmd_generate.generate",
            "generate",
            marks=pytest.mark.skip(reason="generate command not migrated yet"),
        ),
        (
            ["batch-generate", "root-dir"],
            "textfsmgen.tester.cli.cmd_batch_generate.batch_generate",
            "batch-generate",
        ),
        (
            ["batch-regen", "root-dir"],
            "textfsmgen.tester.cli.cmd_batch_regen.batch_regen",
            "batch-regen",
        ),
        (
            ["batch-quicktest", "root-dir"],
            "textfsmgen.tester.cli.cmd_batch_quicktest.batch_quicktest",
            "batch-quicktest",
        ),
        (
            ["merge", "--author", "me", "dst-dir", "src-a", "src-b"],
            "textfsmgen.tester.cli.cmd_merge.merge",
            "merge",
        ),
        (
            ["merge-review", "dst-dir", "src-a", "src-b"],
            "textfsmgen.tester.cli.cmd_merge_review.merge_review",
            "merge-review",
        ),
        (
            ["merge-preview", "src-a", "src-b"],
            "textfsmgen.tester.cli.cmd_merge_preview.merge_preview",
            "merge-preview",
        ),
        (
            ["merge-diff", "src-a", "src-b"],
            "textfsmgen.tester.cli.cmd_merge_diff.merge_diff",
            "merge-diff",
        ),
        (
            ["identical", "src-a", "src-b"],
            "textfsmgen.tester.cli.cmd_identical.run_identical",
            "identical",
        ),
    ],
)
def test_subcommand_invokes_correct_target(runner, argv, target_path, target_name):
    with patch(target_path) as mock_target:
        mock_target.return_value = 0

        result = runner.invoke(cli, argv)

        assert result.exit_code == 0, result.output
        mock_target.assert_called_once()


def test_run_parsing_with_dry_run_and_case(runner):
    with patch("textfsmgen.tester.cli.cmd_run.run") as mock_run:
        mock_run.return_value = 0

        result = runner.invoke(cli, ["run", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        # first arg is Path(case)
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_regen_parsing_with_dry_run(runner):
    with patch("textfsmgen.tester.cli.cmd_regen.regen") as mock_regen:
        mock_regen.return_value = 0

        result = runner.invoke(cli, ["regen", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_regen.assert_called_once()
        args, kwargs = mock_regen.call_args
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_quicktest_parsing_with_dry_run(runner):
    with patch("textfsmgen.tester.cli.cmd_quicktest.quicktest") as mock_qt:
        mock_qt.return_value = 0

        result = runner.invoke(cli, ["quicktest", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_qt.assert_called_once()
        args, kwargs = mock_qt.call_args
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_copy_parsing_flags(runner):
    with patch("textfsmgen.tester.cli.cmd_copy.copy_case") as mock_copy:
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
    with patch(
        "textfsmgen.tester.cli.cmd_new_from_input.new_from_input"
    ) as mock_new_in:
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
    with patch("textfsmgen.tester.cli.cmd_merge_preview.merge_preview") as mock_mp:
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
    with patch("textfsmgen.tester.cli.cmd_merge_diff.merge_diff") as mock_md:
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
    with patch("textfsmgen.tester.cli.cmd_identical.run_identical") as mock_ident:
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
