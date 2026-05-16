import argparse
import pytest

from textfsmgen.tester.cli import TesterCLI  # adjust import to your actual module


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    cli = TesterCLI()
    return cli._build_parser()  # noqa


@pytest.mark.parametrize(
    "argv, expected_action, expected_func_attr",
    [
        (["run", "case-dir"], "run", "_dispatch_run"),
        (["regen", "case-dir"], "regen", "_dispatch_regen"),
        (["diff", "case-dir"], "diff", "_dispatch_diff"),
        (["drift", "case-dir"], "drift", "_dispatch_drift"),
        (["quicktest", "case-dir"], "quicktest", "_dispatch_quicktest"),
        (["copy", "me", "src-dir", "dst-dir"], "copy", "_dispatch_copy"),
        (["duplicate", "me", "src-dir"], "duplicate", "_dispatch_duplicate"),
        (["new", "case-dir"], "new", "_dispatch_new"),
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
            "new-from-input",
            "_dispatch_new_from_input",
        ),
        (["generate", "case-dir"], "generate", "_dispatch_generate"),
        (["batch-generate", "root-dir"], "batch-generate", "_dispatch_batch_generate"),
        (["batch-regen", "root-dir"], "batch-regen", "_dispatch_batch_regen"),
        (
            ["batch-quicktest", "root-dir"],
            "batch-quicktest",
            "_dispatch_batch_quicktest",
        ),
        (
            ["merge", "--author", "me", "dst-dir", "src-a", "src-b"],
            "merge",
            "_dispatch_merge",
        ),
        (
            ["merge-review", "dst-dir", "src-a", "src-b"],
            "merge-review",
            "_dispatch_merge_review",
        ),
        (
            ["merge-preview", "src-a", "src-b"],
            "merge-preview",
            "_dispatch_merge_preview",
        ),
        (
            ["merge-diff", "src-a", "src-b"],
            "merge-diff",
            "_dispatch_merge_diff",
        ),
        (
            ["identical", "src-a", "src-b"],
            "identical",
            "_dispatch_identical",
        ),
    ],
)
def test_subcommand_binds_correct_dispatcher(
    parser, argv, expected_action, expected_func_attr
):
    args = parser.parse_args(argv)
    # action is stored in dest="action"
    assert args.action == expected_action
    # func is bound to the correct dispatcher method
    assert hasattr(args, "func")
    assert args.func.__name__ == expected_func_attr


def test_run_parsing_with_dry_run_and_case_list(parser):
    # run uses nargs=1 for case in your current implementation
    args = parser.parse_args(["run", "--dry-run", "case-dir"])
    assert args.action == "run"
    assert args.dry_run is True
    # because of nargs=1, case is a list
    assert args.case == ["case-dir"]


def test_regen_parsing_with_dry_run(parser):
    args = parser.parse_args(["regen", "--dry-run", "case-dir"])
    assert args.action == "regen"
    assert args.dry_run is True
    assert args.case == ["case-dir"]


def test_diff_parsing(parser):
    args = parser.parse_args(["diff", "case-dir"])
    assert args.action == "diff"
    # diff.case is a plain string (no nargs=1)
    assert args.case == "case-dir"


def test_drift_parsing(parser):
    args = parser.parse_args(["drift", "case-dir"])
    assert args.action == "drift"
    assert args.case == "case-dir"


def test_quicktest_parsing(parser):
    args = parser.parse_args(["quicktest", "case-dir"])
    assert args.action == "quicktest"
    assert args.case == ["case-dir"]


def test_copy_parsing_flags(parser):
    args = parser.parse_args(
        ["copy", "--dry-run", "--force", "me", "src-dir", "dst-dir"]
    )
    assert args.action == "copy"
    assert args.author == "me"
    assert args.src == "src-dir"
    assert args.dst == "dst-dir"
    assert args.dry_run is True
    assert args.force is True


def test_duplicate_parsing_flags(parser):
    args = parser.parse_args(["duplicate", "--dry-run", "--force", "me", "src-dir"])
    assert args.action == "duplicate"
    assert args.author == "me"
    assert args.src == "src-dir"
    assert args.dry_run is True
    assert args.force is True


def test_new_from_input_required_flags(parser):
    args = parser.parse_args(
        [
            "new-from-input",
            "--builder",
            "mybuilder",
            "--author",
            "me",
            "case-dir",
            "inputs-dir",
        ]
    )
    assert args.action == "new-from-input"
    assert args.builder == "mybuilder"
    assert args.author == "me"
    assert args.case == ["case-dir"]
    assert args.inputs == ["inputs-dir"]


def test_merge_preview_compact_and_json(parser):
    args = parser.parse_args(["merge-preview", "--compact", "--json", "src-a", "src-b"])
    assert args.action == "merge-preview"
    assert args.compact is True
    assert args.json is True
    assert args.srcs == ["src-a", "src-b"]


def test_merge_diff_flags(parser):
    args = parser.parse_args(
        [
            "merge-diff",
            "--compact",
            "--json",
            "--diff-count",
            "5",
            "--diff-names-only",
            "src-a",
            "src-b",
        ]
    )
    assert args.action == "merge-diff"
    assert args.compact is True
    # in your current parser, this is stored as is_json
    assert args.is_json is True
    assert args.diff_count == 5
    assert args.diff_names_only is True
    assert args.srcs == ["src-a", "src-b"]


def test_identical_modes(parser):
    args = parser.parse_args(["identical", "--compact", "--json", "src-a", "src-b"])
    assert args.action == "identical"
    assert args.compact is True
    assert args.json is True
    assert args.srcs == ["src-a", "src-b"]
