import click
from pathlib import Path

from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
    integration_only,
)
from .shared import discover_cases


@click.command(
    name="batch-quicktest",
    help="Run `quicktest` on all integration cases under a directory.",
)
@timed_command
@validate_sandbox_flags
@integration_only
@click.argument("base")
@click.option(
    "--sandbox",
    is_flag=True,
    help="Run each case inside <case>.temp and delete on success.",
)
@click.option(
    "--sandbox-keep",
    is_flag=True,
    help="Run each case inside <case>.temp and preserve temp.",
)
@click.option(
    "--summary", is_flag=True, help="Show summary after processing all cases."
)
@click.option("--verbose", is_flag=True, help="Show detailed quicktest steps.")
def cmd_batch_quicktest(base, sandbox, sandbox_keep, summary, verbose):
    """
    Batch version of `quicktest` — processes all integration cases under <base>.
    """

    from .run import cmd_run_ as quicktest_single

    base_dir = Path(base).resolve()
    if not base_dir.exists():
        raise click.ClickException(f"Directory does not exist: {base_dir}")

    cases = list(discover_cases(base_dir))
    if not cases:
        raise click.ClickException(
            f"No valid golden test cases found under: {base_dir}"
        )

    passed = []
    failed = []
    for gc in cases:
        if verbose:
            click.echo(f"\n[info] Processing case: {gc.name}")

        try:
            quicktest_single(
                gc.case_dir,
                sandbox=sandbox,
                sandbox_keep=sandbox_keep,
                quicktest=True,
                # verbose=verbose,
            )
            passed.append(gc)
        except Exception as e:
            failed.append(gc)
            click.echo(f"[FAIL] {gc.name}: {e}")

    if summary:
        click.echo("\n==================== SUMMARY ====================")
        click.echo(f"Total cases: {len(cases)}")
        click.echo(f"Passed     : {len(passed)}")
        click.echo(f"Failed     : {len(failed)}")
        if failed:
            click.echo("\nFailed cases:")
            for gc in failed:
                click.echo(f"  - {gc.name}")
        click.echo("=================================================\n")

    if failed:
        raise click.ClickException("Some cases failed during batch-quicktest.")


# Required for test suite patching
cmd_batch_quicktest.batch_quicktest = cmd_batch_quicktest
