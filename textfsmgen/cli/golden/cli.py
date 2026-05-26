# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path
import click
from typing import cast

from .cli_decorator import validate_sandbox_flags, timed_command

from .commands.diff import cmd_diff
from .commands.drift import cmd_drift

from .commands.duplicate import cmd_duplicate
from .commands.new import cmd_new
from .commands.generate import cmd_generate
from .commands.batch_generate import cmd_batch_generate
from .commands.batch_regen import cmd_batch_regen
from .commands.batch_quicktest import cmd_batch_quicktest

from .commands import (
    run as cmd_run,
    regen as cmd_regen,
    copy as cmd_copy,
    merge as cmd_merge,
    merge_review as cmd_merge_review,
    merge_preview as cmd_merge_preview,
    merge_diff as cmd_merge_diff,
    identical as cmd_identical,
)

__version__ = "1.0.0"

__all__ = [
    "cli",
    "__version__",
]


@click.group(
    help="Golden test utilities for TextFSMGen.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(
    version=__version__,
    prog_name="textfsmgen-golden-tests",
    message="%(prog)s %(version)s",
)
@click.option("--time", is_flag=True, help="Show execution time for the command.")
@click.pass_context
def cli(ctx, time):
    """Golden test utilities for TextFSMGen."""
    ctx.ensure_object(dict)
    ctx.obj["time"] = time


@cli.command(name="version", help="Show the Golden Tests CLI version.")
def version():
    click.echo(f"textfsmgen-golden-tests {__version__}")


@cli.command(help="Run a golden test case in normal, sandbox, or quicktest modes.")
@timed_command
@validate_sandbox_flags
@click.option(
    "--sandbox",
    is_flag=True,
    help="Run inside <case>.temp and delete the sandbox on success.",
)
@click.option(
    "--sandbox-keep",
    is_flag=True,
    help="Run inside <case>.temp and preserve the sandbox directory.",
)
@click.option(
    "--quicktest",
    is_flag=True,
    help="Run a fast, no-write, logic-only validation (no temp dirs).",
)
@click.argument("case", type=click.Path())
def run(sandbox, sandbox_keep, quicktest, case):
    """Execute a golden test case."""
    return cmd_run.run(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        quicktest=quicktest,
    )


@cli.command(help="Regen a golden test case in normal, sandbox, or dryrun.")
@timed_command
@validate_sandbox_flags
@click.option(
    "--sandbox",
    is_flag=True,
    help="Run regen inside <case>.temp and delete it on success.",
)
@click.option(
    "--sandbox-keep",
    is_flag=True,
    help="Run regen inside <case>.temp and preserve it.",
)
@click.option(
    "--dry-run",
    "--dryrun",
    is_flag=True,
    help="Simulate what would be regenerated without writing files.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files without confirmation.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed internal steps during regen.",
)
@click.argument("case", type=click.Path())
def regen(sandbox, sandbox_keep, dry_run, force, case, verbose):
    """Regenerate authoritative golden artifacts for a test case."""
    return cmd_regen.regen(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        force=force,
        verbose=verbose,
    )


@cli.command()
@timed_command
@validate_sandbox_flags
@click.argument("src", type=click.Path(exists=True, file_okay=False))
@click.argument("dst", type=click.Path())
@click.option("--author", required=True, help="Set the author for the new case.")
@click.option(
    "--sandbox", is_flag=True, help="Copy into <dst>.temp and delete temp on success."
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Copy into <dst>.temp and preserve it."
)
@click.option(
    "--dry-run",
    "--dryrun",
    is_flag=True,
    help="Simulate the copy without writing anything.",
)
@click.option(
    "--no-quicktest", is_flag=True, help="Skip running a quick test after copying."
)
@click.option(
    "--open",
    "open_after",
    is_flag=True,
    help="Open the new case directory after creation.",
)
@click.option("--verbose", is_flag=True, help="Show detailed copy operations.")
def copy(
    src, dst, author, sandbox, sandbox_keep, dry_run, no_quicktest, open_after, verbose
):
    """Copy a golden test case into a new case directory."""

    return cmd_copy.copy(
        src=Path(src),
        dst=Path(dst),
        author=author,
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        no_quicktest=no_quicktest,
        open_after=open_after,
        verbose=verbose,
    )


cli.add_command(cast(click.Command, cmd_diff))
cli.add_command(cast(click.Command, cmd_drift))
cli.add_command(cast(click.Command, cmd_duplicate))
cli.add_command(cast(click.Command, cmd_new))
cli.add_command(cast(click.Command, cmd_generate))
cli.add_command(cast(click.Command, cmd_batch_generate))
cli.add_command(cast(click.Command, cmd_batch_regen))
cli.add_command(cast(click.Command, cmd_batch_quicktest))


@cli.command()
@click.option("--dry-run", is_flag=True)
@click.option("--author", required=True)
@click.argument("dst")
@click.argument("srcs", nargs=-1)
def merge(dry_run, author, dst, srcs):
    """Merge multiple integration cases into a new destination case."""
    return cmd_merge.merge(
        Path(dst),
        [Path(p) for p in srcs],
        author=author,
        dry_run=dry_run,
    )


@cli.command("merge-review")
@click.argument("dst")
@click.argument("srcs", nargs=-1)
def merge_review(dst, srcs):
    """Preview a merge using <dst> as the reference case."""
    return cmd_merge_review.merge_review(Path(dst), [Path(p) for p in srcs])


@cli.command("merge-preview")
@click.option("--compact", is_flag=True)
@click.option("--json", "is_json", is_flag=True)
@click.argument("srcs", nargs=-1)
def merge_preview(compact, is_json, srcs):
    """Preview a merge by selecting a reference candidate."""
    return cmd_merge_preview.merge_preview(
        [Path(p) for p in srcs],
        compact=compact,
        is_json=is_json,
    )


@cli.command("merge-diff")
@click.option("--compact", is_flag=True)
@click.option("--json", "is_json", is_flag=True)
@click.option("--diff-count", type=int, default=2)
@click.option("--diff-names-only", is_flag=True)
@click.argument("srcs", nargs=-1)
def merge_diff(compact, is_json, diff_count, diff_names_only, srcs):
    """Diff merged expected_results against golden expected_results."""
    return cmd_merge_diff.merge_diff(
        [Path(p) for p in srcs],
        compact=compact,
        is_json=is_json,
        diff_count=diff_count,
        diff_names_only=diff_names_only,
    )


@cli.command()
@click.option("--compact", is_flag=True)
@click.option("--json", is_flag=True)
@click.argument("srcs", nargs=-1)
def identical(compact, json, srcs):
    """Identify integration cases that produce identical results."""
    return cmd_identical.run_identical(
        [Path(p) for p in srcs],
        compact=compact,
        is_json=json,
    )
