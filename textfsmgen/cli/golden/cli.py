from __future__ import annotations

import json
from pathlib import Path
import click

import time as time_module
import functools

from .commands import (
    run as cmd_run,
    regen as cmd_regen,
    diff as cmd_diff,
    drift as cmd_drift,
    copy as cmd_copy,
    duplicate as cmd_duplicate,
    new as cmd_new,
    new_from_input as cmd_new_from_input,
    generate as cmd_generate,
    batch_generate as cmd_batch_generate,
    batch_regen as cmd_batch_regen,
    batch_quicktest as cmd_batch_quicktest,
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


def timed_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time_module.perf_counter()
        rc = func(*args, **kwargs)
        end = time_module.perf_counter()

        ctx = click.get_current_context(silent=True)
        if ctx and ctx.obj and ctx.obj.get("time"):
            elapsed = end - start
            click.echo(f"[TIME] Completed in {elapsed:.3f}s")

        return rc

    return wrapper


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


@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Run regen inside <case>.temp and delete it on success.",
)
@click.argument("case", type=click.Path())
def regen(dry_run, case):
    """Regenerate derived artifacts for a golden test case."""
    return cmd_regen.regen(Path(case).resolve(), dry_run=dry_run)


@cli.command()
@click.argument("case", type=click.Path())
def diff(case):
    """Show differences between expected and generated results."""
    return cmd_diff.diff(Path(case).resolve())


@cli.command()
@click.argument("case", type=click.Path())
def drift(case):
    """Detect drift between current outputs and golden expected results."""
    return cmd_drift.drift(Path(case).resolve())


@cli.command()
@click.argument("author")
@click.argument("src", type=click.Path())
@click.argument("dst")
@click.option(
    "--dry-run", is_flag=True, help="Copy into <dst>.temp and delete temp on success."
)
@click.option(
    "--force", is_flag=True, help="Allow overwriting an existing destination directory."
)
def copy(author, src, dst, dry_run, force):
    """Copy a golden test case into a new case directory."""
    return cmd_copy.copy_case(
        author=author,
        src=Path(src),
        dst=Path(dst),
        dry_run=dry_run,
        force=force,
    )


@cli.command()
@click.argument("author")
@click.argument("src", type=click.Path())
@click.option("--dry-run", is_flag=True)
@click.option("--force", is_flag=True)
def duplicate(author, src, dry_run, force):
    """Duplicate a golden test case into an auto-named sibling directory."""
    return cmd_duplicate.duplicate_case(
        author=author,
        src=Path(src),
        dry_run=dry_run,
        force=force,
    )


@cli.command()
@click.argument("case")
@click.option(
    "--force", is_flag=True, help="Overwrite the case directory if it already exists."
)
def new(case, force):
    """Create a new golden test case scaffold."""
    case_path = Path(case).resolve()
    if case_path.exists() and not force:
        click.echo(f"[FAIL] Case directory already exists: {case_path}")
        click.echo("       Use --force to overwrite.")
        return 1
    return cmd_new.new(case_path)


@cli.command("new-from-input")
@click.option("--builder", required=True)
@click.option("--params", default="{}")
@click.option("--author", required=True)
@click.option("--force", is_flag=True)
@click.option("--accept", is_flag=True)
@click.option("--dry-run", is_flag=True)
@click.argument("case")
@click.argument("inputs")
def new_from_input(builder, params, author, force, accept, dry_run, case, inputs):
    """Create a new integration case from an input folder."""
    case_path = Path(case).resolve()
    inputs_dir = Path(inputs).resolve()

    try:
        params_obj = json.loads(params)
    except Exception:
        click.echo("[FAIL] --params must be valid JSON")
        return 1

    return cmd_new_from_input.new_from_input(
        case_path,
        inputs_dir,
        builder=builder,
        params=params_obj,
        author=author,
        accept=accept,
        dry_run=dry_run,
        force=force,
    )


@cli.command()
@click.option("--dry-run", is_flag=True)
@click.argument("case", type=click.Path())
def generate(dry_run, case):
    """Generate expected artifacts for an existing case."""
    case_path = Path(case).resolve()
    if not case_path.exists():
        click.echo(f"[FAIL] Case directory does not exist: {case_path}")
        return 1
    return cmd_generate.generate(case_path, dry_run=dry_run)


@cli.command("batch-generate")
@click.option("--dry-run", is_flag=True)
@click.argument("root", type=click.Path())
def batch_generate(dry_run, root):
    """Run `generate` on all cases inside a directory."""
    return cmd_batch_generate.batch_generate(Path(root).resolve(), dry_run=dry_run)


@cli.command("batch-regen")
@click.option("--dry-run", is_flag=True)
@click.argument("root", type=click.Path())
def batch_regen(dry_run, root):
    """Run `regen` on all cases inside a directory."""
    return cmd_batch_regen.batch_regen(Path(root).resolve(), dry_run=dry_run)


@cli.command("batch-quicktest")
@click.option("--dry-run", is_flag=True)
@click.argument("root", type=click.Path())
def batch_quicktest(dry_run, root):
    """Run quicktest on all cases inside a directory."""
    return cmd_batch_quicktest.batch_quicktest(Path(root).resolve(), dry_run=dry_run)


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
