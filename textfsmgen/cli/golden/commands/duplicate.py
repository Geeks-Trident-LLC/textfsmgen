from __future__ import annotations

import shutil
from pathlib import Path
import click

from textfsmgen.libs import file

from ..core.utils import catch_path_errors
from .copy import copy
from .shared import _open_directory


@catch_path_errors
def duplicate(
    src: Path,
    author: str = "",
    sandbox: bool = False,
    sandbox_keep: bool = False,
    dry_run: bool = False,
    no_quicktest: bool = False,
    open_after: bool = False,
    verbose: bool = False,
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
        return

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
        return

    if sandbox_keep:
        click.echo(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return

    # ------------------------------------------------------------
    # Normal success
    # ------------------------------------------------------------
    click.echo(f"[SUCCESS] Duplicated {category} case to {file.path_name(dst)}")

    if open_after:
        _open_directory(dst)
