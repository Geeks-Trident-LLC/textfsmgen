import click
from pathlib import Path

from ..cli_decorator import (
    timed_command,
    validate_sandbox_flags,
)
from .shared import discover_cases

from .regen import cmd_regen_ as regen_single


@click.command(
    name="batch-regen", help="Run `regen` on all integration cases under a directory."
)
@timed_command
@validate_sandbox_flags
@click.argument("base")
@click.option("--dry-run", is_flag=True, help="Simulate regen without writing files.")
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
@click.option("--verbose", is_flag=True, help="Show detailed regen steps.")
def cmd_batch_regen(base, dry_run, sandbox, sandbox_keep, summary, verbose):
    """
    Batch version of `regen` — processes all integration cases under <base>.
    """

    return cmd_batch_regen_(
        base,
        dry_run=dry_run,
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        summary=summary,
        verbose=verbose,
    )


def cmd_batch_regen_(
    base, dry_run=False, sandbox=False, sandbox_keep=False, summary=False, verbose=False
):

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
            regen_single(
                gc.case_dir,
                dry_run=dry_run,
                sandbox=sandbox,
                sandbox_keep=sandbox_keep,
                verbose=verbose,
            )
            passed.append(gc)
        except Exception as e:
            failed.append(gc)
            click.echo(f"[FAIL] {gc.name}: {e}")
            return 1

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
        raise click.ClickException("Some cases failed during batch-regen.")

    return 0


# Required for test suite patching
cmd_batch_regen.batch_regen = cmd_batch_regen
