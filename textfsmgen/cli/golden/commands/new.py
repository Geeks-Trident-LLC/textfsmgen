from __future__ import annotations

import json
import shutil
from pathlib import Path
import click

from textfsmgen.libs import file
from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)

from .shared import _open_directory


@click.command(name="new")
@timed_command
@validate_sandbox_flags
@click.argument("case", type=str)
@click.option(
    "--builder",
    "builder",
    required=True,
    type=click.Choice(["tabular", "category"]),
    help="Builder type for the new integration case.",
)
@click.option("--author", required=True, help="Author name for manifest.json.")
@click.option(
    "--sandbox",
    is_flag=True,
    help="Create into <case>.temp and delete temp on success.",
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Create into <case>.temp and preserve it."
)
@click.option(
    "--dry-run",
    "--dryrun",
    is_flag=True,
    help="Simulate creation without writing anything.",
)
@click.option(
    "--open",
    "open_after",
    is_flag=True,
    help="Open the new case directory after creation.",
)
@click.option("--verbose", is_flag=True, help="Show detailed creation steps.")
def cmd_new(case, builder, author, sandbox, sandbox_keep, dry_run, open_after, verbose):
    """Create a new INTEGRATION golden test case."""

    # ------------------------------------------------------------
    # Resolve and validate case path
    # ------------------------------------------------------------
    dst = Path(case).resolve()

    # Must contain both golden and integration
    if "golden" not in dst.parts or "integration" not in dst.parts:
        raise click.ClickException(
            f"Invalid case path: {file.path_name(dst)}. Must be inside tests/golden/integration."
        )

    # Ensure correct directory structure: .../golden/integration/<case>
    parts = dst.parts
    idx = parts.index("integration")  # safe because we checked above

    integration_root = Path(*parts[: idx + 1])

    if (
        integration_root.name != "integration"
        or integration_root.parent.name != "golden"
    ):
        raise click.ClickException(
            f"Case must be under tests/golden/integration, got: {file.path_name(dst)}"
        )

    if dry_run:
        click.echo(f"[DRY-RUN] Create integration case → {file.path_name(dst)}")
        click.echo(f"  builder  : {builder}")
        click.echo(f"  author   : {author}")
        click.echo(f"  sandbox  : {sandbox or sandbox_keep}")

        # Still validate existence AFTER printing DRY-RUN
        if dst.exists():
            raise click.ClickException(f"Case already exists: {file.path_name(dst)}")

        return

    # Ensure case does not already exist
    if dst.exists():
        raise click.ClickException(f"Case already exists: {file.path_name(dst)}")

    # ------------------------------------------------------------
    # Sandbox rewrite
    # ------------------------------------------------------------
    real_dst = dst
    if sandbox or sandbox_keep:
        dst = dst.with_name(dst.name + ".temp")
        if verbose:
            click.echo(f"[sandbox] Using temp directory: {file.path_name(dst)}")

    # ------------------------------------------------------------
    # Create directory structure
    # ------------------------------------------------------------
    if verbose:
        click.echo(f"[mkdir] {file.path_name(dst)}")

    (dst / "expected").mkdir(parents=True)
    (dst / "inputs").mkdir()
    (dst / "expected_results").mkdir()

    # Empty template + snippet
    (dst / "expected" / "template.textfsm").write_text("")
    (dst / "expected" / "snippet.txt").write_text("")

    # ------------------------------------------------------------
    # Build manifest.json
    # ------------------------------------------------------------
    from textfsmgen.cli.config_cmd import CONFIG_TYPES

    params = CONFIG_TYPES[builder]["params"]

    manifest = {
        "builder": builder,
        "parameters": params,
        "meta": {
            "author": author,
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }

    (dst / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # ------------------------------------------------------------
    # Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        if verbose:
            click.echo(f"[sandbox] Cleaning up temp directory: {file.path_name(dst)}")
        shutil.rmtree(dst)
        click.echo(
            f"[SUCCESS] sandbox new-case completed for {file.path_name(real_dst.name)}"
        )
        return

    if sandbox_keep:
        click.echo(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return

    # ------------------------------------------------------------
    # Normal success
    # ------------------------------------------------------------
    click.echo(f"[SUCCESS] Created integration case at {file.path_name(dst)}")

    if open_after:
        _open_directory(dst)
