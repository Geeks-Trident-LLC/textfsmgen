from __future__ import annotations

import shutil
from pathlib import Path
import click

from textfsmgen.libs import file

from .copy import copy
from .shared import _open_directory

from ..core.utils import validate_case_path
from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)


@click.command("duplicate", help="Duplicate a golden test case with an auto-generated name (<case>-copy).")
@timed_command
@validate_sandbox_flags
@click.argument("src", type=click.Path(exists=True, file_okay=False))
@click.option("--author", required=True, help="Set the author for the new case.")
@click.option(
    "--sandbox",
    is_flag=True,
    help="Duplicate into <dst>.temp and delete temp on success.",
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Duplicate into <dst>.temp and preserve it."
)
@click.option(
    "--dry-run",
    "--dryrun",
    is_flag=True,
    help="Simulate the duplicate operation without writing anything.",
)
@click.option(
    "--no-quicktest", is_flag=True, help="Skip running a quick test after duplicating."
)
@click.option(
    "--open",
    "open_after",
    is_flag=True,
    help="Open the new case directory after creation.",
)
@click.option("--verbose", is_flag=True, help="Show detailed duplicate operations.")
def cmd_duplicate(
    src, author, sandbox, sandbox_keep, dry_run, no_quicktest, open_after, verbose
):

    # ------------------------------------------------------------
    # Determine category
    # ------------------------------------------------------------
    def detect_category(path: Path) -> str:
        parts = path.parts
        if "main" in parts:
            return "main"
        if "integration" in parts:
            return "integration"
        raise click.ClickException(
            f"Cannot determine category for: {file.path_name(path)}"
        )

    src = Path(src).resolve()
    ok = validate_case_path(src)
    if not ok:
        click.echo(f"[FAIL] {ok}")
        return 1

    category = detect_category(src)

    # ------------------------------------------------------------
    # Auto-generate destination name
    # ------------------------------------------------------------
    parent = src.parent
    base = src.name

    # First try: <name>-copy
    dst = parent / f"{base}-copy"
    counter = 2

    while dst.exists():
        dst = parent / f"{base}-copy-{counter}"
        counter += 1

    # ------------------------------------------------------------
    # Dry-run
    # ------------------------------------------------------------
    if dry_run:
        click.echo(f"[DRY-RUN] Duplicate {file.path_name(src)} → {file.path_name(dst)}")
        click.echo(f"  category : {category}")
        click.echo(f"  author   : {author}")
        click.echo(f"  quicktest: {'no' if no_quicktest else 'yes'}")
        click.echo(f"  regen    : {'yes' if category == 'main' else 'no'}")
        click.echo(f"  sandbox  : {sandbox or sandbox_keep}")
        return 0

    # ------------------------------------------------------------
    # Sandbox destination
    # ------------------------------------------------------------
    real_dst = dst
    if sandbox or sandbox_keep:
        dst = dst.with_name(dst.name + ".temp")
        if verbose:
            click.echo(f"[sandbox] Using temp directory: {file.path_name(dst)}")

    # ------------------------------------------------------------
    # Perform the copy (reuse copy logic)
    # ------------------------------------------------------------

    copy(
        src=src,
        dst=dst,
        author=author,
        no_quicktest=no_quicktest,
        verbose=verbose,
    )

    # ------------------------------------------------------------
    # Auto-regen for main
    # ------------------------------------------------------------
    if category == "main":
        from .regen import regen

        regen(dst)

    # ------------------------------------------------------------
    # Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        if verbose:
            click.echo(f"[sandbox] Cleaning up temp directory: {file.path_name(dst)}")
        shutil.rmtree(dst)
        click.echo(
            f"[SUCCESS] sandbox duplicate completed for {file.path_name(real_dst.name)}"
        )
        return 0

    if sandbox_keep:
        click.echo(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return 0

    # ------------------------------------------------------------
    # Normal success
    # ------------------------------------------------------------
    click.echo(f"[SUCCESS] Duplicated {category} case to {file.path_name(dst)}")

    if open_after:
        _open_directory(dst)

    return 0
