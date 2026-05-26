from __future__ import annotations

import json
import shutil
from pathlib import Path
import click

from textfsmgen.libs import file
from .shared import _open_directory

from ..core.utils import catch_path_errors


@catch_path_errors
def copy(
    src: Path = None,
    dst: Path = None,
    author="",
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    no_quicktest=False,
    open_after=False,
    verbose=False,
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

    src_category = detect_category(src)
    dst_category = detect_category(dst)

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
        return

    # ------------------------------------------------------------
    # Determine actual destination (sandbox or real)
    # ------------------------------------------------------------
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
    # Perform the copy
    # ------------------------------------------------------------
    if verbose:
        click.echo(f"[copy] {file.path_name(src)} → {file.path_name(dst)}")

    shutil.copytree(src, dst)

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
        from .run import run

        rc = run(dst, quicktest=True)
        if rc != 0:
            raise click.ClickException(f"Quicktest failed for copied case: {dst}")

    # ------------------------------------------------------------
    # Auto-regen for MAIN cases
    # ------------------------------------------------------------
    if src_category == "main":
        from .regen import cmd_regen

        cmd_regen(dst)

    # ------------------------------------------------------------
    # Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        if verbose:
            click.echo(f"[sandbox] Cleaning up temp directory: {file.path_name(dst)}")
        shutil.rmtree(dst)
        click.echo(
            f"[SUCCESS] sandbox copy completed for {file.path_name(real_dst.name)}"
        )
        return

    # sandbox-keep → preserve temp directory
    if sandbox_keep:
        click.echo(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return

    # ------------------------------------------------------------
    # Normal success
    # ------------------------------------------------------------
    click.echo(f"[SUCCESS] Copied {src_category} case to {file.path_name(dst)}")

    if open_after:
        _open_directory(dst)
