from __future__ import annotations

from pathlib import Path
import json
import shutil
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors, validate_case_path
from ..cli_decorator import timed_command, validate_sandbox_flags
from .shared import log, short_path, describe_file_update, print_status


@click.command(
    name="run",
    help="Run a golden test case in normal, sandbox, dry-run, or quicktest modes.",
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
    "--dry-run", "--dryrun", is_flag=True, help="Simulate run without writing files."
)
@click.option(
    "--quicktest", is_flag=True, help="Fast logic-only validation (no writes)."
)
@click.option(
    "--author", default="", help="Optional author override for manifest.json."
)
@click.option("--quiet", is_flag=True, help="Suppress non-essential output.")
@click.option("--verbose", is_flag=True, help="Show detailed steps.")
@click.option("--debug", is_flag=True, help="Show developer-level logs.")
@click.option("--compact", is_flag=True, help="Compact summary output only.")
@click.argument("case", type=click.Path())
def cmd_run(
    sandbox,
    sandbox_keep,
    dry_run,
    quicktest,
    author,
    quiet,
    verbose,
    debug,
    compact,
    case,
):
    return cmd_run_(
        Path(case).resolve(),
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        quicktest=quicktest,
        author=author,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )


@catch_path_errors
def cmd_run_(
    case_path: Path,
    *,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    quicktest=False,
    author="",
    quiet=False,
    verbose=False,
    debug=False,
    compact=False,
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

    # ------------------------------------------------------------
    # 3. MAIN CASE WORKFLOW
    # ------------------------------------------------------------
    if case.is_main():
        log(
            f"{short_path(case_path)} — main case",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        canonical = loader.load_canonical()
        sample = canonical.sample.content

        log(
            "validating canonical template",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        built = loader.build(sample)

        log(
            f"template length={len(built.template)} bytes",
            level="debug",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        if built.template != canonical.template.content:
            log(
                "canonical template mismatch",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            return 1

        log(
            "validating canonical snippet",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        if built.snippet != canonical.snippet.content:
            log(
                "canonical snippet mismatch",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            return 1

        log(
            "validating canonical result",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        parsed = parse_textfsm_to_dicts(built.template, sample)
        log(
            f"parsed rows={len(parsed)}",
            level="debug",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        if parsed != canonical.result.content:
            log(
                "canonical result mismatch",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            return 1

        # Validate all inputs
        for inp, exp in loader.load_input_result_pairs():
            log(
                f"validating input: {Path(inp.fullname).name}",
                level="verbose",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            parsed = parse_textfsm_to_dicts(built.template, inp.content)
            log(
                f"parsed rows={len(parsed)}",
                level="debug",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            if parsed != exp.content:
                log(
                    f"input mismatch: {Path(inp.fullname).name}",
                    level="FAIL",
                    quiet=quiet,
                    verbose=verbose,
                    debug=debug,
                    compact=compact,
                )
                return 1

        # Quicktest
        if quicktest:
            log(
                f"{short_path(case_path)} — quicktest OK",
                level="OK",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            if compact:
                print(f"[RUN] {short_path(case_path)} rc=0")
            return 0

        # Dry-run
        if dry_run:
            print("[RUN] DRY-RUN")
            print(f"  case: {short_path(case_path)}")
            print("  would update:")
            print("    manifest.json (if author provided)")
            print("    golden.hash")
            print("    meta.json")
            print("[DRY-RUN] run simulation completed.")
            return 0

        # Write metadata + golden.hash
        log(
            "writing meta.json and golden.hash",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        if author:
            manifest = loader.load_manifest()
            meta = manifest.setdefault("meta", {})
            meta["author"] = author
            meta["email"] = ""
            (case_path / "manifest.json").write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False)
            )

        meta_path = case_path / "meta.json"
        hash_path = case_path / "golden.hash"

        meta_before = meta_path.exists()
        hash_before = hash_path.exists()

        loader.write_meta()
        loader.write_golden_hash()

        meta_status = describe_file_update(meta_path, exist=meta_before)
        hash_status = describe_file_update(hash_path, exist=hash_before)

        print_status(
            f"{short_path(case_path)} — run completed\n"
            f"  Updated: {short_path(meta_path)} ({meta_status})\n"
            f"  Updated: {short_path(hash_path)} ({hash_status})",
            ok=True,
        )

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

        if compact:
            print(f"[RUN] {short_path(case_path)} rc=0")
        return 0

    # ------------------------------------------------------------
    # 4. INTEGRATION CASE WORKFLOW
    # ------------------------------------------------------------
    log(
        f"{short_path(case_path)} — integration case",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    expected = loader.load_expected()

    for inp, exp in loader.load_input_result_pairs():
        log(
            f"validating input: {Path(inp.fullname).name}",
            level="verbose",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        parsed = parse_textfsm_to_dicts(expected.template.content, inp.content)
        log(
            f"parsed rows={len(parsed)}",
            level="debug",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        if parsed != exp.content:
            log(
                f"result mismatch for {Path(inp.fullname).name}",
                level="FAIL",
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )
            return 1

    # Quicktest
    if quicktest:
        log(
            f"{short_path(case_path)} — quicktest OK",
            level="OK",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        if compact:
            print(f"[RUN] {short_path(case_path)} rc=0")
        return 0

    # Dry-run
    if dry_run:
        print("[RUN] DRY-RUN")
        print(f"  case: {short_path(case_path)}")
        print("  integration case: would NOT write anything")
        print("[DRY-RUN] run simulation completed.")
        return 0

    # Normal integration run
    log(
        f"{short_path(case_path)} — run completed (integration, no writes)",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

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

    if compact:
        print(f"[RUN] {short_path(case_path)} rc=0")

    return 0
