import click
from pathlib import Path

from textfsmgen.libs import file
from ..cli_decorator import integration_only, validate_sandbox_flags, timed_command
from .shared import discover_cases


@click.command(
    name="batch-generate",
    help="Run `generate` on all integration cases under a directory.",
)
@timed_command
@validate_sandbox_flags
@integration_only
@click.argument("base", type=click.Path(exists=True, file_okay=False))
@click.option("--author", required=True, help="Set the author for all generated cases.")
@click.option(
    "--dry-run", is_flag=True, help="Simulate generation without writing files."
)
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
@click.option("--verbose", is_flag=True, help="Show detailed generation steps.")
def cmd_batch_generate(base, author, dry_run, sandbox, sandbox_keep, summary, verbose):
    """
    Batch version of `generate` — processes all integration cases under <base>.
    """

    from .generate import cmd_generate_ as generate_single

    base_dir = Path(base).resolve()
    cases = list(discover_cases(base_dir))

    if not cases:
        raise click.ClickException(
            f"No valid golden test cases found under: {file.path_name(base_dir)}"
        )

    if verbose:
        click.echo(
            f"[info] Found {len(cases)} case(s) under {file.path_name(base_dir)}"
        )

    passed = []
    failed = []

    for gc in cases:
        if gc.is_main():
            failed.append(gc)
            click.echo(f"[skip] {gc.name} (not an integration case)")
            continue

        if verbose:
            click.echo(f"\n[info] Processing case: {gc.name}")

        try:
            generate_single(
                gc.case_dir,
                author=author,
                dry_run=dry_run,
                sandbox=sandbox,
                sandbox_keep=sandbox_keep,
                open_after=False,
                verbose=verbose,
                summary=False,
            )
            passed.append(gc)
        except Exception as e:
            failed.append(gc)
            click.echo(f"[FAIL] {gc.name}: {e}")

    # Summary
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

    # Exit code
    if failed:
        raise click.ClickException("Some cases failed during batch-generate.")


# Required for test suite patching
cmd_batch_generate.batch_generate = cmd_batch_generate
