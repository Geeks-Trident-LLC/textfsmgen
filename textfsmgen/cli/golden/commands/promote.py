from __future__ import annotations

from pathlib import Path
import json
import shutil
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command, validate_sandbox_flags
from .shared import log, short_path
from .run import cmd_run_


@click.command(
    name="promote",
    help="Promote an integration case into a main case by generating canonical sample and result.",
)
@timed_command
@validate_sandbox_flags
@click.option("--author", required=True, help="Author of the promoted case (required).")
@click.option("--email", default="", help="Email metadata for manifest.json.")
@click.option("--notes", default="", help="Notes metadata for manifest.json.")
@click.option(
    "--description", default="", help="Description metadata for manifest.json."
)
@click.option(
    "--dry-run",
    "--dryrun",
    is_flag=True,
    help="Simulate promotion without writing files.",
)
@click.option(
    "--sandbox",
    is_flag=True,
    help="Run promotion inside <case>.temp and delete on success.",
)
@click.option(
    "--sandbox-keep",
    is_flag=True,
    help="Run promotion inside <case>.temp and preserve it.",
)
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.option("--summary", is_flag=True, help="Show summary of promotion.")
@click.argument("case", type=click.Path(exists=True))
def cmd_promote(
    case,
    author,
    email,
    notes,
    description,
    dry_run,
    sandbox,
    sandbox_keep,
    quiet,
    verbose,
    debug,
    compact,
    summary,
):
    return cmd_promote_(
        case_path=Path(case).resolve(),
        author=author,
        email=email,
        notes=notes,
        description=description,
        dry_run=dry_run,
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
        summary=summary,
    )


def cmd_promote_(
    case_path: Path,
    *,
    author: str,
    email: str,
    notes: str,
    description: str,
    dry_run=False,
    sandbox=False,
    sandbox_keep=False,
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
    summary=False,
):
    # ------------------------------------------------------------
    # 0. Resolve sandbox destination
    # ------------------------------------------------------------
    real_dst = None
    if sandbox or sandbox_keep:
        real_dst = case_path
        case_path = case_path.with_name(case_path.name + ".temp")

        log(
            f"Using sandbox directory: {short_path(case_path)}",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        if case_path.exists():
            shutil.rmtree(case_path)

    # ------------------------------------------------------------
    # 1. Load and validate integration case (using run(...quicktest=True))
    # ------------------------------------------------------------
    case = GoldenCase.from_path(
        case_path if (sandbox or sandbox_keep) else real_dst or case_path
    )

    if not case.is_integration():
        raise click.ClickException(
            f"{short_path(case.case_dir)} is not an integration case"
        )

    rc = cmd_run_(
        case.case_dir,
        quicktest=True,
        # quiet=quiet,
        # verbose=verbose,
        # debug=debug,
        # compact=compact,
    )
    if rc != 0:
        raise click.ClickException(f"{short_path(case.case_dir)} failed quicktest")

    log(
        f"{short_path(case.case_dir)} — integration and tested",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 2. Determine promote path (integration → main)
    # ------------------------------------------------------------
    parts = list(case.case_dir.parts)
    try:
        idx = parts.index("integration")
    except ValueError:
        raise click.ClickException("Path does not contain 'integration'")

    parts[idx] = "main"
    promote_path = Path(*parts)

    if promote_path.exists():
        raise click.ClickException(
            f"Main case already exists: {short_path(promote_path)}"
        )

    # ------------------------------------------------------------
    # 3. Find canonical sample by loader.build(sample)
    # ------------------------------------------------------------
    loader = case.data
    expected = loader.load_expected()
    expected_template = expected.template.content

    canonical_sample = None
    canonical_result = None

    for inp in loader.load_inputs():
        sample = inp.content
        name = Path(inp.fullname).name

        log(
            f"trying sample: {name}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        built = loader.build(sample)
        generated_template = built.template

        if generated_template == expected_template:
            log(
                f"canonical sample found: {name}",
                level="SUCCESS",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            canonical_sample = sample
            canonical_result = parse_textfsm_to_dicts(generated_template, sample)
            break

    if canonical_sample is None:
        raise click.ClickException(
            "No input sample can reproduce expected template; cannot promote."
        )

    # ------------------------------------------------------------
    # DRY-RUN: stop here
    # ------------------------------------------------------------
    if dry_run:
        log(
            "promotion simulation completed.",
            level="DRY-RUN",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 0

    # ------------------------------------------------------------
    # 4. Create promote directory structure
    # ------------------------------------------------------------
    promote_path.mkdir(parents=True)

    canonical_dir = promote_path / "canonical"
    canonical_dir.mkdir()

    inputs_dir = promote_path / "inputs"
    expected_results_dir = promote_path / "expected_results"

    inputs_dir.mkdir()
    expected_results_dir.mkdir()

    # ------------------------------------------------------------
    # 5. Write manifest.json (apply metadata)
    # ------------------------------------------------------------
    manifest = loader.load_manifest()
    meta = manifest.setdefault("meta", {})
    meta["author"] = author
    meta["email"] = email
    meta["notes"] = notes
    meta["description"] = description

    (promote_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )

    # ------------------------------------------------------------
    # 6. Write canonical template + snippet
    # ------------------------------------------------------------
    (canonical_dir / "textfsm.template").write_text(expected.template.content)
    (canonical_dir / "snippet.txt").write_text(expected.snippet.content)

    # ------------------------------------------------------------
    # 7. Write canonical sample + result
    # ------------------------------------------------------------
    (canonical_dir / "sample.txt").write_text(canonical_sample)
    (canonical_dir / "result.json").write_text(
        json.dumps(canonical_result, indent=2, ensure_ascii=False)
    )

    # ------------------------------------------------------------
    # 8. Copy inputs
    # ------------------------------------------------------------
    for inp in loader.load_inputs():
        name = Path(inp.fullname).name
        (inputs_dir / name).write_text(inp.content)

    # ------------------------------------------------------------
    # 9. Copy expected_results
    # ------------------------------------------------------------
    for _, exp in loader.load_input_result_pairs():
        name = Path(exp.fullname).name
        (expected_results_dir / name).write_text(
            json.dumps(exp.content, indent=2, ensure_ascii=False)
        )

    # ------------------------------------------------------------
    # 10. Run quicktest on promoted case (must generate golden.hash/meta.json)
    # ------------------------------------------------------------
    rc = cmd_run_(
        promote_path,
        # quiet=quiet,
        # verbose=verbose,
        # debug=debug,
        # compact=compact,
    )

    if rc != 0:
        shutil.rmtree(promote_path)
        raise click.ClickException(
            "Promoted case failed quicktest (golden.hash/meta.json not valid)"
        )

    # ------------------------------------------------------------
    # 11. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        shutil.rmtree(case_path)
        log(
            f"sandbox promotion completed for {short_path(promote_path)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 0

    if sandbox_keep:
        log(
            f"sandbox-keep: preserved {short_path(case_path)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 0

    # ------------------------------------------------------------
    # 12. Compact mode
    # ------------------------------------------------------------
    if compact:
        print(f"[PROMOTE] Case: {short_path(case.case_dir)}")
        print(f"[PROMOTE] Promoted: {short_path(promote_path)}")
        print("[PROMOTE] Result: success")
        return 0

    # ------------------------------------------------------------
    # 13. Summary mode
    # ------------------------------------------------------------
    if summary:
        print("===== PROMOTE SUMMARY =====")
        print(f"source:   {short_path(case.case_dir)}")
        print(f"promoted: {short_path(promote_path)}")
        print("canonical:")
        print("  template: canonical/textfsm.template")
        print("  snippet:  canonical/snippet.txt")
        print("  sample:   canonical/sample.txt")
        print("  result:   canonical/result.json")
        print("===========================")
        return 0

    # ------------------------------------------------------------
    # 14. Normal output
    # ------------------------------------------------------------
    log(
        f"promotion completed: {short_path(promote_path)}",
        level="SUCCESS",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    return 0
