from __future__ import annotations

from pathlib import Path
import json
import shutil
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors, validate_case_path
from ..cli_decorator import timed_command, validate_sandbox_flags
from .shared import log, short_path, print_status


@click.command(
    name="promote-plan",
    help="Preview what promote WOULD do — no writes, no side effects.",
)
@timed_command
@validate_sandbox_flags
@click.option(
    "--sandbox", is_flag=True, help="Run inside <case>.temp and delete on success."
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Run inside <case>.temp and preserve it."
)
@click.option(
    "--dry-run", "--dryrun", is_flag=True, help="Simulate promote-plan itself."
)
@click.option("--author", default="", help="Preview author metadata.")
@click.option("--email", default="", help="Preview email metadata.")
@click.option("--notes", default="", help="Preview notes metadata.")
@click.option("--description", default="", help="Preview description metadata.")
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.option(
    "--json", "json_output", is_flag=True, help="Output machine-readable JSON summary."
)
@click.argument("case", type=click.Path())
def cmd_promote_plan(
    sandbox,
    sandbox_keep,
    dry_run,
    author,
    email,
    notes,
    description,
    quiet,
    verbose,
    debug,
    compact,
    json_output,
    case,
):
    return cmd_promote_plan_(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        author=author,
        email=email,
        notes=notes,
        description=description,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
        json_output=json_output,
    )


@catch_path_errors
def cmd_promote_plan_(
    case_path: Path,
    *,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    author="",
    email="",
    notes="",
    description="",
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
    json_output=False,
) -> int:

    # ------------------------------------------------------------
    # 0. Validate case path
    # ------------------------------------------------------------
    ok = validate_case_path(case_path)
    if not ok:
        log(
            f"{ok}",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 1

    log(
        f"Loading case: {short_path(case_path)}",
        level="debug",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 1. Sandbox setup
    # ------------------------------------------------------------
    real_case_path = case_path
    case_temp = None

    if sandbox or sandbox_keep:
        case_temp = real_case_path.with_name(real_case_path.name + ".temp")

        log(
            f"[sandbox] copying case to {short_path(case_temp)}",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        if case_temp.exists():
            shutil.rmtree(case_temp)

        shutil.copytree(real_case_path, case_temp)
        case_path = case_temp

    # ------------------------------------------------------------
    # 2. Load case
    # ------------------------------------------------------------
    case = GoldenCase.from_path(case_path)
    loader = case.data

    if not case.is_integration():
        log(
            f"{short_path(case_path)} is not an integration case",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 1

    log(
        f"{short_path(case_path)} — integration case",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 3. Determine promote path
    # ------------------------------------------------------------
    parts = list(case_path.parts)
    idx = parts.index("integration")
    parts[idx] = "main"
    promote_path = Path(*parts)

    log(
        f"promote-path would be: {short_path(promote_path)}",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    if promote_path.exists():
        log(
            f"main case already exists: {short_path(promote_path)}",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        promotable = False
    else:
        promotable = True

    # ------------------------------------------------------------
    # 4. Find canonical sample
    # ------------------------------------------------------------
    expected = loader.load_expected()
    expected_template = expected.template.content

    canonical_sample = None
    canonical_result = None
    canonical_name = None

    for inp in loader.load_inputs():
        name = Path(inp.fullname).name
        sample = inp.content

        log(
            f"trying sample: {name}",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        built = loader.build(sample)

        if built.template == expected_template:
            canonical_sample = sample
            canonical_result = parse_textfsm_to_dicts(built.template, sample)
            canonical_name = name

            log(
                f"canonical sample found: {name}",
                level="SUCCESS",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            break

    if canonical_sample is None:
        log(
            "no canonical sample found — cannot promote",
            level="FAIL",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        promotable = False

    # ------------------------------------------------------------
    # 5. Validate all inputs
    # ------------------------------------------------------------
    input_mismatches = []

    for inp, exp in loader.load_input_result_pairs():
        parsed = parse_textfsm_to_dicts(expected.template.content, inp.content)
        if parsed != exp.content:
            input_mismatches.append(Path(inp.fullname).name)

    if input_mismatches:
        promotable = False
        for name in input_mismatches:
            log(
                f"result mismatch for {name}",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

    # ------------------------------------------------------------
    # 6. Metadata preview
    # ------------------------------------------------------------
    metadata_preview = {
        "author": author or "(unchanged)",
        "email": email or "(unchanged)",
        "notes": notes or "(unchanged)",
        "description": description or "(unchanged)",
    }

    log(
        f"metadata preview: {metadata_preview}",
        level="verbose",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 7. JSON output
    # ------------------------------------------------------------
    if json_output:
        summary = {
            "case": short_path(case_path),
            "promote_path": short_path(promote_path),
            "promotable": promotable,
            "canonical_sample": canonical_name,
            "canonical_rows": len(canonical_result) if canonical_result else 0,
            "input_mismatches": input_mismatches,
            "metadata_preview": metadata_preview,
        }
        print(json.dumps(summary, indent=2))
        return 0 if promotable else 1

    # ------------------------------------------------------------
    # 8. Dry-run
    # ------------------------------------------------------------
    if dry_run:
        print("[PROMOTE-PLAN] DRY-RUN")
        print(f"  source:        {short_path(case_path)}")
        print(f"  promote-path:  {short_path(promote_path)}")
        print(f"  canonical:     {canonical_name}")
        print(f"  promotable:    {promotable}")
        print("  metadata preview:")
        for k, v in metadata_preview.items():
            print(f"    {k}: {v}")
        print("[DRY-RUN] promote-plan simulation completed.")
        return 0 if promotable else 1

    # ------------------------------------------------------------
    # 9. Compact summary
    # ------------------------------------------------------------
    if compact:
        print(f"[PROMOTE-PLAN] {short_path(case_path)} promotable={promotable}")
        return 0 if promotable else 1

    # ------------------------------------------------------------
    # 10. Normal output
    # ------------------------------------------------------------
    print_status(
        f"[PROMOTE-PLAN]\n"
        f"  source:        {short_path(case_path)}\n"
        f"  promote-path:  {short_path(promote_path)}\n"
        f"  canonical:     {canonical_name}\n"
        f"  promotable:    {promotable}\n",
        ok=promotable,
    )

    # ------------------------------------------------------------
    # 11. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        shutil.rmtree(case_temp)
        log(
            "[sandbox] cleaned up sandbox directory",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    return 0 if promotable else 1
