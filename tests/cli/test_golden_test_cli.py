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
        "copy": "copy",
        "duplicate": "duplicate",
        "new": "new",
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
        (["run", "--sandbox", "case-dir"], "run"),
        (["regen", "--dry-run", "case-dir"], "regen"),
        (["diff", "case-dir"], "diff"),
        (["drift", "case-dir"], "drift"),
        (["new", "--author", "dummy-user", "--builder", "category", "case-dir"], "new"),
        (["batch-regen", "root-dir"], "batch_regen"),
        (["batch-quicktest", "root-dir"], "batch_quicktest"),
        (["merge", "--author", "dummy-user", "dst", "src-a", "src-b"], "merge"),
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


def test_run_parsing_with_sandbox_and_case(runner):
    with patch_cmd("run") as mock_run:
        mock_run.return_value = 0

        result = runner.invoke(cli, ["run", "--sandbox", "case-dir"])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        # first arg is Path(case)
        assert str(args[0]).endswith("case-dir")
        assert kwargs["sandbox"] is True


def test_regen_parsing_with_dry_run(runner):
    with patch_cmd("regen") as mock_regen:
        mock_regen.return_value = 0

        result = runner.invoke(cli, ["regen", "--dry-run", "case-dir"])

        assert result.exit_code == 0
        mock_regen.assert_called_once()
        args, kwargs = mock_regen.call_args
        assert str(args[0]).endswith("case-dir")
        assert kwargs["dry_run"] is True


def test_copy_parsing_flags(runner, tmp_path):
    src = tmp_path / "tests/golden/integration/src-dir"
    dst = tmp_path / "tests/golden/integration/dst-dir"

    src.mkdir(parents=True)  # required because click.Path(exists=True)

    with patch_cmd("copy") as mock_copy:
        mock_copy.return_value = 0

        result = runner.invoke(
            cli,
            [
                "copy",
                "--dry-run",
                "--author",
                "dummy-user",
                src.as_posix(),
                dst.as_posix(),
            ],
        )

        assert result.exit_code == 0
        mock_copy.assert_called_once()
        args, kwargs = mock_copy.call_args

        assert kwargs["author"] == "dummy-user"
        assert str(kwargs["src"].as_posix()).endswith(src.as_posix())
        assert str(kwargs["dst"].as_posix()).endswith(dst.as_posix())
        assert kwargs["dry_run"] is True


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
