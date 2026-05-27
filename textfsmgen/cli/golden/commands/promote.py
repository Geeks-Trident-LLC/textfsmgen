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


def _sandbox_cleanup(
    case_temp: Path, promote_temp: Path, keep: bool, quiet, verbose, debug, compact
):
    """Remove or preserve sandbox directories."""
    if keep:
        log(
            "[sandbox-keep] preserved sandbox directories:",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        log(
            f"  {short_path(case_temp)}",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        log(
            f"  {short_path(promote_temp)}",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return

    # Remove both sandbox dirs
    if case_temp.exists():
        shutil.rmtree(case_temp)
    if promote_temp.exists():
        shutil.rmtree(promote_temp)

    log(
        "[sandbox] cleaned up sandbox directories",
        level="sandbox",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


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
    "--dry-run", is_flag=True, help="Simulate promotion without writing files."
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
    # 0. Sandbox setup
    # ------------------------------------------------------------
    real_case_path = case_path
    case_temp = None

    if sandbox or sandbox_keep:
        case_temp = real_case_path.with_name(real_case_path.name + ".temp")

        log(
            f"Using sandbox directory: {short_path(case_temp)}",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        if case_temp.exists():
            shutil.rmtree(case_temp)

        shutil.copytree(real_case_path, case_temp)
        case_path = case_temp

    # ------------------------------------------------------------
    # 1. Validate integration case via full quicktest
    # ------------------------------------------------------------
    case = GoldenCase.from_path(case_path)

    if not case.is_integration():
        if sandbox or sandbox_keep:
            _sandbox_cleanup(
                case_temp,
                case_temp,
                keep=sandbox_keep,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
        raise click.ClickException(
            f"{short_path(case_path)} is not an integration case"
        )

    rc = cmd_run_(
        case_path,
        quicktest=True,
        # quiet=quiet,
        # verbose=verbose,
        # debug=debug,
        # compact=compact,
    )
    if rc != 0:
        if sandbox or sandbox_keep:
            _sandbox_cleanup(
                case_temp,
                case_temp,
                keep=sandbox_keep,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
        raise click.ClickException(f"{short_path(case_path)} failed quicktest")

    log(
        f"{short_path(case_path)} — integration and tested",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 2. Determine promote path (integration → main)
    # ------------------------------------------------------------
    parts = list(case_path.parts)
    idx = parts.index("integration")
    parts[idx] = "main"
    promote_path = Path(*parts)

    promote_temp = promote_path

    if promote_path.exists():
        if sandbox or sandbox_keep:
            _sandbox_cleanup(
                case_temp,
                promote_temp,
                keep=sandbox_keep,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
        raise click.ClickException(
            f"Main case already exists: {short_path(promote_path)}"
        )

    # ------------------------------------------------------------
    # 3. Find canonical sample
    # ------------------------------------------------------------
    loader = case.data
    expected = loader.load_expected()
    expected_template = expected.template.content

    canonical_sample = None
    canonical_result = None
    canonical_name = None

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
        if sandbox or sandbox_keep:
            _sandbox_cleanup(
                case_temp,
                promote_temp,
                keep=sandbox_keep,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
        raise click.ClickException(
            "No input sample can reproduce expected template; cannot promote."
        )

    # ------------------------------------------------------------
    # DRY-RUN
    # ------------------------------------------------------------
    if dry_run:
        print("[PROMOTE] DRY-RUN")
        print(f"  source:          {short_path(case_path)}")
        print(f"  promote-path:    {short_path(promote_path)}")
        print(f"  canonical sample: {canonical_name}")
        print(f"  canonical result: {len(canonical_result)} rows")
        print("  manifest metadata:")
        print(f"    author:       {author}")
        print(f"    email:        {email}")
        print(f"    notes:        {notes}")
        print(f"    description:  {description}")
        print("  would write:")
        print("    manifest.json")
        print("    canonical/textfsm.template")
        print("    canonical/snippet.txt")
        print("    canonical/sample.txt")
        print("    canonical/result.json")
        print(f"    inputs/* ({len(loader.load_inputs())} files)")
        print(
            f"    expected_results/* ({len(list(loader.load_input_result_pairs()))} files)"
        )
        print("  would run quicktest on promoted case")
        print("[DRY-RUN] promotion simulation completed.")
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
    # 5. Write manifest.json with metadata
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
    # 6. Write canonical artifacts
    # ------------------------------------------------------------
    (canonical_dir / "textfsm.template").write_text(expected.template.content)
    (canonical_dir / "snippet.txt").write_text(expected.snippet.content)
    (canonical_dir / "sample.txt").write_text(canonical_sample)
    (canonical_dir / "result.json").write_text(
        json.dumps(canonical_result, indent=2, ensure_ascii=False)
    )

    # ------------------------------------------------------------
    # 7. Copy inputs
    # ------------------------------------------------------------
    for inp in loader.load_inputs():
        name = Path(inp.fullname).name
        (inputs_dir / name).write_text(inp.content)

    # ------------------------------------------------------------
    # 8. Copy expected_results
    # ------------------------------------------------------------
    for _, exp in loader.load_input_result_pairs():
        name = Path(exp.fullname).name
        (expected_results_dir / name).write_text(
            json.dumps(exp.content, indent=2, ensure_ascii=False)
        )

    # ------------------------------------------------------------
    # 9. Ensure expected/ exists before quicktest
    # ------------------------------------------------------------
    expected_dir = promote_path / "expected"
    expected_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------
    # 10. Run quicktest on promoted case
    # ------------------------------------------------------------
    rc = cmd_run_(
        promote_path,
        # quiet=quiet,
        # verbose=verbose,
        # debug=debug,
        # compact=compact,
    )

    if rc != 0:
        if sandbox or sandbox_keep:
            _sandbox_cleanup(
                case_temp,
                promote_temp,
                keep=sandbox_keep,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
        raise click.ClickException(
            "Promoted case failed quicktest (golden.hash/meta.json not valid)"
        )

    # ------------------------------------------------------------
    # 11. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox or sandbox_keep:
        _sandbox_cleanup(
            case_temp,
            promote_temp,
            keep=sandbox_keep,
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
        print(f"[PROMOTE] Case: {short_path(case_path)}")
        print(f"[PROMOTE] Promoted: {short_path(promote_path)}")
        print("[PROMOTE] Result: success")
        return 0

    # ------------------------------------------------------------
    # 13. Summary mode
    # ------------------------------------------------------------
    if summary:
        print("===== PROMOTE SUMMARY =====")
        print(f"source:   {short_path(case_path)}")
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
