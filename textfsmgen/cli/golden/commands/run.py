"""
Implementation of:

    textfsmgen tester run <case>

This action performs a non-destructive test run.

MAIN CASE:
    - Writes meta.json
    - Writes golden.hash

INTEGRATION CASE:
    - Writes nothing

NEVER writes inside:
    canonical/
    expected/
    expected_results/
    inputs/
"""

from __future__ import annotations

from pathlib import Path
import shutil

import click

from .shared import run_canonical, run_expected
from ..core.utils import catch_path_errors

from ..core.golden_case import GoldenCase

from textfsmgen.libs import file

from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)
from ..core.utils import validate_case_path


@click.command(
    name="run", help="Run a golden test case in normal, sandbox, or quicktest modes."
)
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
def cmd_run(sandbox, sandbox_keep, quicktest, case):
    """Execute a golden test case."""
    return cmd_run_(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        quicktest=quicktest,
    )


@catch_path_errors
def cmd_run_(
    case_path: Path,
    *,
    sandbox: bool = False,
    sandbox_keep: bool = False,
    quicktest: bool = False,
) -> int:

    ok = validate_case_path(case_path)
    if not ok:
        click.echo(f"[FAIL] {ok}")
        return 1

    # --------------------------------------------------------------
    # Quicktest: fast, no writes, no temp dirs
    # --------------------------------------------------------------
    if quicktest:
        case = GoldenCase.from_path(case_path)
        return (
            run_canonical(case, quicktest=True)
            if case.is_main()
            else run_expected(case, quicktest=True)
        )

    # --------------------------------------------------------------
    # Sandbox modes: create <case>.temp and run inside it
    # --------------------------------------------------------------
    if sandbox or sandbox_keep:
        temp_path = case_path.with_name(case_path.name + ".temp")
        click.echo(f"[sandbox] Using temporary directory: {file.path_name(temp_path)}")

        if temp_path.exists():
            shutil.rmtree(temp_path)

        shutil.copytree(case_path, temp_path)
        case_path = temp_path

        case = GoldenCase.from_path(case_path)
        rc = (
            run_canonical(case, quicktest=False)
            if case.is_main()
            else run_expected(case, quicktest=False)
        )

        if sandbox:
            if rc == 0:
                click.echo("[sandbox] Cleaning up temporary directory.")
                shutil.rmtree(case_path)
            else:
                click.echo("[sandbox] Run failed. Temporary directory preserved.")
        else:
            click.echo("[sandbox] Preserving temporary directory.")

        return rc

    # --------------------------------------------------------------
    # Normal run (in-place)
    # --------------------------------------------------------------
    case = GoldenCase.from_path(case_path)
    return (
        run_canonical(case, quicktest=False)
        if case.is_main()
        else run_expected(case, quicktest=False)
    )
