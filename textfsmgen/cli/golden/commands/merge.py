from __future__ import annotations

import json
import shutil
from pathlib import Path
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command, validate_sandbox_flags
from ..core.utils import validate_case_path
from .shared import _open_directory, log, short_path


# ======================================================================
# CLI ENTRYPOINT
# ======================================================================


@click.command(
    name="merge", help="Merge multiple integration cases into a new destination case."
)
@timed_command
@validate_sandbox_flags
@click.option(
    "--sandbox",
    is_flag=True,
    help="Run merge inside <dst>.temp and delete it on success.",
)
@click.option(
    "--sandbox-keep", is_flag=True, help="Run merge inside <dst>.temp and preserve it."
)
@click.option(
    "--dry-run", "--dryrun", is_flag=True, help="Simulate merge without writing files."
)
@click.option("--force", is_flag=True, help="Overwrite existing sandbox directory.")
@click.option(
    "--summary", is_flag=True, help="Show summary of merged inputs and results."
)
@click.option("--verbose", is_flag=True, help="Show detailed merge steps.")
@click.option("--debug", is_flag=True, help="Show ultra-verbose developer logs.")
@click.option("--quiet", is_flag=True, help="Suppress all non-essential output.")
@click.option("--author", help="Set author metadata for the merged case.")
@click.option(
    "--open",
    "open_after",
    is_flag=True,
    help="Open the merged case directory after completion.",
)
@click.argument("dst", type=click.Path())
@click.argument("srcs", nargs=-1, type=click.Path(exists=True))
def cmd_merge(
    dst,
    srcs,
    sandbox,
    sandbox_keep,
    dry_run,
    force,
    summary,
    verbose,
    debug,
    quiet,
    author,
    open_after,
):
    return cmd_merge_(
        dst=Path(dst).resolve(),
        src_paths=[Path(s).resolve() for s in srcs],
        sandbox=sandbox,
        sandbox_keep=sandbox_keep,
        dry_run=dry_run,
        force=force,
        summary=summary,
        verbose=verbose,
        debug=debug,
        quiet=quiet,
        author=author,
        open_after=open_after,
    )


# ======================================================================
# MAIN IMPLEMENTATION
# ======================================================================


def cmd_merge_(
    dst: Path,
    src_paths: list[Path],
    *,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    force=False,
    summary=False,
    verbose=False,
    debug=False,
    quiet=False,
    author=None,
    open_after=False,
):
    # ------------------------------------------------------------
    # 0. Resolve sandbox destination
    # ------------------------------------------------------------

    real_dst = dst
    if sandbox or sandbox_keep:
        dst = dst.with_name(dst.name + ".temp")
        log(
            f"Using sandbox directory: {short_path(dst)}",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        if dst.exists() and not force:
            raise click.ClickException(
                f"Sandbox directory {short_path(dst)} already exists. Use --force to overwrite."
            )

        if dst.exists():
            shutil.rmtree(dst)

    # ------------------------------------------------------------
    # 1. dst must not exist (normal mode)
    # ------------------------------------------------------------
    if not (sandbox or sandbox_keep) and dst.exists():
        raise click.ClickException(f"Destination already exists: {short_path(dst)}")

    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # Load GoldenCase objects
    cases = [GoldenCase.from_path(p) for p in src_paths]

    # ------------------------------------------------------------
    # 2. Validate all cases
    # ------------------------------------------------------------
    builder = cases[0].data.load_manifest().get("builder", "")
    log(f"builder = {builder}", level="OK", quiet=quiet, verbose=verbose, debug=debug)

    for c in cases:
        log(
            f"validating source: {short_path(c.case_dir)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

        ok = validate_case_path(c.case_dir)
        if not ok:
            raise click.ClickException(f"[FAIL] {ok}")

        if not c.is_integration():
            raise click.ClickException(
                f"[FAIL] merge is only supported for integration cases: {short_path(c.case_dir)}"
            )

        try:
            c.tested()
        except Exception as e:
            raise click.ClickException(
                f"[FAIL] case {short_path(c.case_dir)} is not tested:\n{e}"
            )

        log(
            f"{short_path(c.case_dir)} — tested and compatible",
            level="OK",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

    # Cross-check all pairs
    for outer in cases:
        for inner in cases:
            if outer is inner:
                continue
            outer.check(inner)

    # ------------------------------------------------------------
    # 3. Find reference template + snippet
    # ------------------------------------------------------------
    log(
        "evaluating reference candidates...",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    reference, diagnostics = _find_reference_case(cases, verbose, debug, quiet)

    for diag in diagnostics:
        print(diag)

    log(
        f"Reference case selected: {short_path(reference.case_dir)}",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    ref_loader = reference.data
    ref_template = ref_loader.load_expected().template.content
    ref_snippet = ref_loader.load_expected().snippet.content

    # ------------------------------------------------------------
    # DRY-RUN: stop here
    # ------------------------------------------------------------
    if dry_run:
        log(
            "merge simulation completed.",
            level="DRY-RUN",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )
        return 0

    # ------------------------------------------------------------
    # 4. Create dst structure
    # ------------------------------------------------------------
    log(
        f"creating destination case: {short_path(dst)}",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    (dst / "inputs").mkdir(parents=True)
    (dst / "expected").mkdir(parents=True)
    (dst / "expected_results").mkdir(parents=True)

    # ------------------------------------------------------------
    # 5. Merge inputs
    # ------------------------------------------------------------
    log("merging inputs...", level="info", quiet=quiet, verbose=verbose, debug=debug)

    merged_inputs, rename_logs = _merge_inputs(dst, cases, verbose, debug, quiet)

    for log_line in rename_logs:
        print(log_line)

    # ------------------------------------------------------------
    # 6. Write reference template + snippet
    # ------------------------------------------------------------
    log(
        "writing template and snippet...",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    (dst / "expected" / "textfsm.template").write_text(ref_template)
    (dst / "expected" / "snippet.txt").write_text(ref_snippet)

    # ------------------------------------------------------------
    # 7. Generate expected_results
    # ------------------------------------------------------------
    log(
        "generating expected_results...",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    written_results = _write_expected_results(
        dst, merged_inputs, ref_template, verbose, debug, quiet
    )

    # ------------------------------------------------------------
    # 8. Write metadata
    # ------------------------------------------------------------
    meta = {
        "author": author or "",
        "notes": "",
        "description": "",
    }
    (dst / "meta.json").write_text(json.dumps(meta, indent=2))

    # ------------------------------------------------------------
    # 9. Summary
    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # 9. Summary
    # ------------------------------------------------------------
    if summary:
        # Summary should always print regardless of quiet/verbose/debug
        log(
            "===== MERGE SUMMARY =====",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        log(
            f"reference case: {short_path(reference.case_dir)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        log(
            f"inputs merged: {len(merged_inputs)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        for p in merged_inputs:
            print(f"  - {short_path(p)}")

        log(
            f"expected results: {len(written_results)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

        for p in written_results:
            print(f"  - {short_path(p)}")

        log(
            "=========================",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
        )

    # ------------------------------------------------------------
    # 10. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        log(
            "cleaning up sandbox directory.",
            level="sandbox",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )
        shutil.rmtree(dst)
        log(
            f"sandbox merge completed for {short_path(real_dst)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )
        return 0

    if sandbox_keep:
        log(
            f"sandbox-keep: preserved {short_path(dst)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )
        return 0

    # ------------------------------------------------------------
    # 11. Normal success
    # ------------------------------------------------------------
    log(
        f"merge completed: {short_path(dst)}",
        level="SUCCESS",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
    )

    if open_after:
        _open_directory(dst)

    return 0


# ======================================================================
# INTERNAL HELPERS
# ======================================================================


def _find_reference_case(cases, verbose, debug, quiet):
    diagnostics = []

    for candidate in cases:
        cand_name = short_path(candidate.case_dir)
        diagnostics.append(f"[info]   trying: {cand_name}")

        cand_loader = candidate.data
        cand_template = cand_loader.load_expected().template.content

        failures = []

        for other in cases:
            for input_info, exp_info in other.data.load_input_result_pairs():
                rows = parse_textfsm_to_dicts(cand_template, input_info.content)
                if rows != exp_info.content:
                    failures.append(
                        f"[warn]       failed to parse {short_path(input_info.fullname)} "
                        f"from {short_path(other.case_dir)}"
                    )

        if failures:
            diagnostics.extend(failures)
            continue

        diagnostics.append(f"[OK]       {cand_name} is a valid reference candidate")
        return candidate, diagnostics

    raise click.ClickException("[FAIL] no valid reference case found.")


def _merge_inputs(dst, cases, verbose, debug, quiet):
    dst_inputs = dst / "inputs"
    merged = {}
    logs = []

    for case in cases:
        for inp in case.data.load_inputs():
            name = Path(inp.fullname).name
            content = inp.content

            if name not in merged:
                merged[name] = content
                logs.append(f"[OK]     {name} — added")
                continue

            if merged[name] == content:
                logs.append(f"[OK]     {name} — identical, kept")
                continue

            base = Path(name).stem
            ext = Path(name).suffix
            counter = 2

            while True:
                new_name = f"{base}_{counter}{ext}"
                if new_name not in merged:
                    merged[new_name] = content
                    logs.append(f"[rename] {name} → {new_name} (content differs)")
                    break
                counter += 1

    written = []
    for name, content in merged.items():
        out_path = dst_inputs / name
        out_path.write_text(content)
        written.append(out_path)

    return written, logs


def _write_expected_results(dst, merged_inputs, template, verbose, debug, quiet):
    out_dir = dst / "expected_results"
    written = []

    for inp_path in merged_inputs:
        sample = inp_path.read_text()
        rows = parse_textfsm_to_dicts(template, sample)

        stem = inp_path.stem
        out_path = out_dir / f"{stem}_result.json"
        out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        written.append(out_path)

        log(
            f"{short_path(inp_path)} → {short_path(out_path)} ({len(rows)} rows)",
            level="OK",
            indent=4,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
        )

    return written
