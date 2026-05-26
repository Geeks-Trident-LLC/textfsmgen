"""
Regenerate *derived artifacts* for a golden test case.

Derived artifacts:
  MAIN CASE:
      expected_results/*.json
      meta.json
      golden.hash

  INTEGRATION CASE:
      expected/snippet.txt
      expected/textfsm.template
      expected_results/*.json

Authoritative data (never modified):
      canonical/
      inputs/
      manifest.json

Modes:
  Normal (default):
      Regenerate derived artifacts in-place.

  --sandbox:
      Run regen inside <case>.temp and delete it on success.

  --sandbox-keep:
      Run regen inside <case>.temp and preserve it.

  --dry-run:
      Show what would be regenerated without writing files.

Sandbox rules:
  • <case>.temp is created as a working copy.
  • If it already exists, --force is required to overwrite.
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..core.golden_case import GoldenCase

from ..core.data_loader import extract_subpath_after

from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)
from ..core.utils import validate_case_path

# ---------------------------------------------------------------------------
# MAIN ENTRYPOINT
# ---------------------------------------------------------------------------


@click.command(
    name="regen", help="Regen a golden test case in normal, sandbox, or dryrun."
)
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
def cmd_regen(case, sandbox, sandbox_keep, dry_run, force, verbose):
    return cmd_regen_(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        force=force,
        verbose=verbose,
    )


def cmd_regen_(
    case_path,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    force=False,
    verbose=False,
):
    ok = validate_case_path(case_path)
    if not ok:
        click.echo(f"[FAIL] {ok}")
        return 1

    _v("Resolved case path:", verbose, path=case_path)

    # --------------------------------------------------------------
    # Sandbox mode
    # --------------------------------------------------------------
    if sandbox or sandbox_keep:
        temp_path = case_path.with_name(case_path.name + ".temp")

        click.echo(f"[sandbox] Using temporary directory: {file.path_name(temp_path)}")
        _v("Preparing sandbox directory", verbose)

        if temp_path.exists():
            _v("Found existing sandbox directory:", verbose, path=temp_path)
            if not force:
                click.echo(
                    f"[FAIL] Sandbox directory {file.path_name(temp_path)!r} already exists. "
                    "Use --force to overwrite it.",
                )
                return 1
            _v("Overwriting existing sandbox directory (--force)", verbose)
            shutil.rmtree(temp_path)

        _v("Copying case into sandbox directory", verbose)
        shutil.copytree(case_path, temp_path)

        case_path = temp_path
        case = GoldenCase.from_path(case_path)
        _v("Loaded sandbox case:", verbose, path=case_path)

        rc = _dispatch_regen(case, dry_run=dry_run, verbose=verbose)

        if sandbox:
            if rc == 0:
                click.echo("[sandbox] Cleaning up temporary directory.")
                _v("Removing sandbox directory after successful regen", verbose)
                shutil.rmtree(case_path)
            else:
                click.echo(
                    "[FAIL] Regen failed. Temporary directory preserved for inspection."
                )
        else:
            click.echo("[sandbox] Preserving temporary directory.")
            _v("Sandbox-keep: leaving temp directory intact", verbose)

        return rc

    # --------------------------------------------------------------
    # Normal regen
    # --------------------------------------------------------------
    _v("Performing normal regen (no sandbox)", verbose)
    case = GoldenCase.from_path(case_path)
    return _dispatch_regen(case, dry_run=dry_run, verbose=verbose)


# ---------------------------------------------------------------------------
# VERBOSE HELPER
# ---------------------------------------------------------------------------


def _v(message: str, verbose: bool, *, path: Path | None = None, case_name: str = ""):
    """Print a verbose message with optional path formatting."""
    if not verbose:
        return

    if path is None:
        click.echo(f"[OK] {message}")
        return

    path = Path(path)
    case_name = case_name or "golden"
    rel = file.path_name(extract_subpath_after(case_name, path))
    click.echo(f"[OK] {message} {rel}")


# ---------------------------------------------------------------------------
# DISPATCH
# ---------------------------------------------------------------------------


def _dispatch_regen(case: GoldenCase, *, dry_run: bool, verbose: bool) -> int:
    """Dispatch to main or integration regen."""
    if case.is_main():
        return regen_main(case, dry_run=dry_run, verbose=verbose)
    return regen_integration(case, dry_run=dry_run, verbose=verbose)


# ---------------------------------------------------------------------------
# MAIN CASE REGEN
# ---------------------------------------------------------------------------


def regen_main(case: GoldenCase, dry_run=False, verbose=False) -> int:
    _v("MAIN case detected", verbose)

    loader = case.data
    canonical = loader.load_canonical()
    _v("Loaded canonical snippet/template", verbose)

    updated = []
    case_name = case.case_dir.name

    for input_info in loader.load_inputs():
        _v("Processing input:", verbose, path=input_info.fullname, case_name=case_name)

        base = Path(input_info.fullname).stem
        out_path = loader.case_dir / "expected_results" / f"{base}_result.json"

        rows = parse_textfsm_to_dicts(canonical.template.content, input_info.content)
        _v(f"Parsed {len(rows)} rows from input", verbose)

        if not dry_run:
            _v("Writing expected results:", verbose, path=out_path, case_name=case_name)
            out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))

        updated.append(file.path_name(out_path))

    if not dry_run:
        _v("Writing meta.json", verbose)
        loader.write_meta()
    updated.append(file.path_name(case.case_dir / "meta.json"))

    if not dry_run:
        _v("Writing golden.hash", verbose)
        loader.write_golden_hash()
    updated.append(file.path_name(case.case_dir / "golden.hash"))

    _print(case, updated, dry_run=dry_run)
    return 0


# ---------------------------------------------------------------------------
# INTEGRATION CASE REGEN
# ---------------------------------------------------------------------------


def regen_integration(case: GoldenCase, dry_run=False, verbose=False) -> int:
    _v("INTEGRATION case detected:", verbose, path=case.case_dir)

    loader = case.data
    expected = loader.load_expected()

    updated = []
    snippet_written = False
    case_name = case.case_dir.name

    for input_info in loader.load_inputs():
        _v("Processing input:", verbose, path=input_info.fullname, case_name=case_name)

        builder = loader.build(input_info.content)
        if not builder:
            click.echo(
                f"[FAIL] cannot build from input: {file.path_name(input_info.fullname)}"
            )
            return 1

        if not snippet_written:
            _v("Writing snippet and template", verbose)
            if not dry_run:
                Path(expected.snippet.fullname).write_text(builder.snippet)
                Path(expected.template.fullname).write_text(builder.template)

            updated.append(file.path_name(expected.snippet.fullname))
            updated.append(file.path_name(expected.template.fullname))
            snippet_written = True

        base = Path(input_info.fullname).stem
        out_path = loader.case_dir / "expected_results" / f"{base}_result.json"

        rows = parse_textfsm_to_dicts(builder.template, input_info.content)
        _v(f"Parsed {len(rows)} rows from input", verbose)

        if not dry_run:
            _v("Writing expected results:", verbose, path=out_path, case_name=case_name)
            out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))

        updated.append(file.path_name(out_path))

    _print(case, updated, dry_run=dry_run)
    return 0


# ---------------------------------------------------------------------------
# PRINT SUMMARY
# ---------------------------------------------------------------------------


def _print(case: GoldenCase, files: list[str], dry_run=False) -> None:
    tc_name = extract_subpath_after("golden", case.case_dir)
    prefix = "[DRY-RUN]" if dry_run else "[SUCCESS]"
    click.echo(f"{prefix} regenerated {file.path_name(tc_name)}")
    for f in files:
        click.echo(f"  - {file.path_name(f)}")
