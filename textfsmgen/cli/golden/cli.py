# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path
import click
from typing import cast

from .commands.run import cmd_run
from .commands.regen import cmd_regen
from .commands.diff import cmd_diff
from .commands.drift import cmd_drift
from .commands.copy import cmd_copy
from .commands.duplicate import cmd_duplicate
from .commands.new import cmd_new
from .commands.generate import cmd_generate
from .commands.batch_generate import cmd_batch_generate
from .commands.batch_regen import cmd_batch_regen
from .commands.batch_quicktest import cmd_batch_quicktest
from .commands.merge import cmd_merge

from .commands import (
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


cli.add_command(cast(click.Command, cmd_run))
cli.add_command(cast(click.Command, cmd_regen))
cli.add_command(cast(click.Command, cmd_diff))
cli.add_command(cast(click.Command, cmd_drift))
cli.add_command(cast(click.Command, cmd_copy))
cli.add_command(cast(click.Command, cmd_duplicate))
cli.add_command(cast(click.Command, cmd_new))
cli.add_command(cast(click.Command, cmd_generate))
cli.add_command(cast(click.Command, cmd_batch_generate))
cli.add_command(cast(click.Command, cmd_batch_regen))
cli.add_command(cast(click.Command, cmd_batch_quicktest))

cli.add_command(cast(click.Command, cmd_merge))


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
