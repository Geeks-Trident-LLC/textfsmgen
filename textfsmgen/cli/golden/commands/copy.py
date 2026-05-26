from __future__ import annotations

import json
import shutil
from pathlib import Path

import click

from textfsmgen.libs import file
from .shared import _open_directory
from ..core.utils import catch_path_errors, validate_case_path
from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)


@click.command(name="copy", help="Copy a golden test case into a new case directory.")
@timed_command
@validate_sandbox_flags
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
@click.argument("src", type=click.Path(exists=True, file_okay=False))
@click.argument("dst", type=click.Path())
def cmd_copy(
    src, dst, author, sandbox, sandbox_keep, dry_run, no_quicktest, open_after, verbose
):
    """Copy a golden test case into a new case directory."""

    return cmd_copy_(
        src=Path(src).resolve(),
        dst=Path(dst).resolve(),
        author=author,
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        no_quicktest=no_quicktest,
        open_after=open_after,
        verbose=verbose,
    )


@catch_path_errors
def cmd_copy_(
    src: Path | None = None,
    dst: Path | None = None,
    author: str = "",
    sandbox: bool = False,
    sandbox_keep: bool = False,
    dry_run: bool = False,
    no_quicktest: bool = False,
    open_after: bool = False,
    verbose: bool = False,
):
    # ------------------------------------------------------------
    # Determine category from SRC
    # ------------------------------------------------------------
    def detect_category(path: Path) -> str:
        parts = path.parts
        if "main" in parts:
            return "main"
        if "integration" in parts:
            return "integration"
        raise click.ClickException(f"Cannot determine category for: {path}")

    ok = validate_case_path(src)
    if not ok:
        click.echo(f"[FAIL] {ok}")
        return 1

    src_category = detect_category(src)
    # Destination is logically the same category as source
    # (we only prevent explicit cross-category paths)
    try:
        dst_category = detect_category(dst)
    except click.ClickException:
        dst_category = src_category

    if src_category != dst_category:
        raise click.ClickException(
            f"Cannot copy between categories: {src_category} → {dst_category}"
        )

    # ------------------------------------------------------------
    # Dry-run: show what would happen
    # ------------------------------------------------------------
    if dry_run:
        click.echo(f"[DRY-RUN] Copy {file.path_name(src)} → {file.path_name(dst)}")
        click.echo(f"  category : {src_category}")
        click.echo(f"  author   : {author}")
        click.echo(f"  quicktest: {'no' if no_quicktest else 'yes'}")
        click.echo(f"  regen    : {'yes' if src_category == 'main' else 'no'}")
        click.echo(f"  sandbox  : {sandbox or sandbox_keep}")
        return 0

    # ------------------------------------------------------------
    # Determine actual destination (sandbox or real)
    # ------------------------------------------------------------
    real_dst: Path | None = None
    if sandbox or sandbox_keep:
        real_dst = dst
        dst = dst.with_name(dst.name + ".temp")
        if verbose:
            click.echo(f"[sandbox] Using temp directory: {file.path_name(dst)}")

    # ------------------------------------------------------------
    # Ensure destination does not exist
    # ------------------------------------------------------------
    if dst.exists():
        raise click.ClickException(f"Destination already exists: {file.path_name(dst)}")

    # ------------------------------------------------------------
    # Perform the copy (full tree, then fix metadata)
    # ------------------------------------------------------------
    if verbose:
        click.echo(f"[copy] {file.path_name(src)} → {file.path_name(dst)}")

    shutil.copytree(src, dst)

    # Remove golden.hash if present (force new golden lifecycle)
    golden_hash = dst / "golden.hash"
    if golden_hash.exists():
        golden_hash.unlink()

    # ------------------------------------------------------------
    # Update metadata
    # ------------------------------------------------------------
    meta_path = dst / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {}

    meta["author"] = author
    meta["notes"] = ""
    meta["description"] = ""

    meta_path.write_text(json.dumps(meta, indent=2))

    # ------------------------------------------------------------
    # Quicktest (optional)
    # ------------------------------------------------------------
    if not no_quicktest:
        from .run import cmd_run_

        rc = cmd_run_(dst, quicktest=True)
        if rc != 0:
            raise click.ClickException(f"Quicktest failed for copied case: {dst}")

    # ------------------------------------------------------------
    # Auto-regen for MAIN cases
    # ------------------------------------------------------------
    if src_category == "main":
        from .regen import cmd_regen_

        cmd_regen_(dst)

    # ------------------------------------------------------------
    # Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        if verbose:
            click.echo(f"[sandbox] Cleaning up temp directory: {file.path_name(dst)}")
        shutil.rmtree(dst)
        target = real_dst if real_dst is not None else dst
        click.echo(f"[SUCCESS] sandbox copy completed for {file.path_name(target)}")
        return 0

    if sandbox_keep:
        click.echo(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return 0

    # ------------------------------------------------------------
    # Normal success
    # ------------------------------------------------------------
    click.echo(f"[SUCCESS] Copied {src_category} case to {file.path_name(dst)}")

    if open_after:
        _open_directory(dst)

    return 0
