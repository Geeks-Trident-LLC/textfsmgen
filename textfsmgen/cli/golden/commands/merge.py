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
@click.option("--compact", is_flag=True, help="Compact summary output only.")
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
    compact,
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
        compact=compact,
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
    compact=False,
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

    # Debug: manifest
    log(
        f"manifest: {cases[0].data.load_manifest()}",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 2. Validate all cases
    # ------------------------------------------------------------
    builder = cases[0].data.load_manifest().get("builder", "")
    log(
        f"builder = {builder}",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    validation_failures = []

    for c in cases:
        log(
            f"validating source: {short_path(c.case_dir)}",
            level="info",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        ok = validate_case_path(c.case_dir)
        if not ok:
            validation_failures.append(f"[FAIL] {ok}")
            continue

        if not c.is_integration():
            validation_failures.append(
                f"[FAIL] merge is only supported for integration cases: {short_path(c.case_dir)}"
            )
            continue

        try:
            c.tested()
        except Exception as e:
            validation_failures.append(
                f"[FAIL] case {short_path(c.case_dir)} is not tested:\n{e}"
            )
            continue

        log(
            f"{short_path(c.case_dir)} — tested and compatible",
            level="OK",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

    if validation_failures:
        if compact:
            print("[MERGE] Reference: (none)")
            print("[MERGE] Result: fail")
            return 1

        for msg in validation_failures:
            log(
                msg,
                level="FAIL",
                quiet=False,
                verbose=True,
                debug=debug,
                compact=compact,
            )
        return 1

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
        compact=compact,
    )

    reference, diagnostics = _find_reference_case(cases, verbose, debug, quiet)

    if reference is None:
        if compact:
            print("[MERGE] Reference: (none)")
            print("[MERGE] Result: fail")
        else:
            if not quiet and not compact:
                for diag in diagnostics:
                    print(diag)
            log(
                "no valid reference candidates found",
                level="FAIL",
                quiet=False,
                verbose=True,
                debug=debug,
                compact=compact,
            )
        return 1

    if not quiet and not compact:
        for diag in diagnostics:
            print(diag)

    log(
        f"Reference case selected: {short_path(reference.case_dir)}",
        level="OK",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
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
            compact=compact,
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
        compact=compact,
    )

    (dst / "inputs").mkdir(parents=True)
    (dst / "expected").mkdir(parents=True)
    (dst / "expected_results").mkdir(parents=True)

    log(
        "created directories: inputs/, expected/, expected_results/",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 5. Merge inputs
    # ------------------------------------------------------------
    log(
        "merging inputs...",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    merged_inputs, rename_logs = _merge_inputs(
        dst, cases, verbose, debug, quiet, compact
    )

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
        compact=compact,
    )

    (dst / "expected" / "textfsm.template").write_text(ref_template)
    (dst / "expected" / "snippet.txt").write_text(ref_snippet)

    log(
        f"template length = {len(ref_template)} bytes",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )
    log(
        f"snippet length = {len(ref_snippet)} bytes",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 7. Generate expected_results
    # ------------------------------------------------------------
    log(
        "generating expected_results...",
        level="info",
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    written_results = _write_expected_results(
        dst, merged_inputs, ref_template, verbose, debug, quiet, compact
    )

    # ------------------------------------------------------------
    # 8. Write manifest.json (correct behavior)
    # ------------------------------------------------------------
    # Use manifest from the first src case as the base
    manifest = cases[0].data.load_manifest()

    # Update meta fields
    meta = manifest.setdefault("meta", {})
    meta["author"] = author or ""
    meta["email"] = ""
    meta["notes"] = ""
    meta["description"] = ""

    log(
        f"manifest meta updated: {meta}",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # Write manifest.json
    manifest_path = dst / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    log(
        f"wrote manifest.json → {short_path(manifest_path)}",
        level="OK",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    # ------------------------------------------------------------
    # 5. Compact mode
    # ------------------------------------------------------------
    if compact:
        print(f"[MERGE] Reference: {short_path(reference.case_dir)}")
        print(f"[MERGE] Inputs: {len(merged_inputs)}")
        print("[MERGE] Result: success")
        return 0

    # ------------------------------------------------------------
    # 9. Summary
    # ------------------------------------------------------------
    if summary:
        # Summary always prints regardless of quiet/verbose
        log(
            "===== MERGE SUMMARY =====",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )
        log(
            f"reference case: {short_path(reference.case_dir)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )
        log(
            f"inputs merged: {len(merged_inputs)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )
        for p in merged_inputs:
            print(f"  - {short_path(p)}")
        log(
            f"expected results: {len(written_results)}",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
        )
        for p in written_results:
            print(f"  - {short_path(p)}")
        log(
            "=========================",
            level="info",
            quiet=False,
            verbose=True,
            debug=debug,
            compact=compact,
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
            compact=compact,
        )

        log(
            f"removing sandbox directory: {short_path(dst)}",
            level="debug",
            indent=2,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

        shutil.rmtree(dst)

        log(
            f"sandbox merge completed for {short_path(real_dst)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )
        return 0

    if sandbox_keep:
        log(
            f"sandbox-keep: preserved {short_path(dst)}",
            level="SUCCESS",
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
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
        compact=compact,
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

        # Debug: template length
        diagnostics.append(
            f"[debug]     candidate {cand_name}: template length = {len(cand_template)} bytes"
        )

        failures = []

        for other in cases:
            for input_info, exp_info in other.data.load_input_result_pairs():
                diagnostics.append(
                    f"[debug]       comparing against {short_path(input_info.fullname)}"
                )

                rows = parse_textfsm_to_dicts(cand_template, input_info.content)

                if rows != exp_info.content:
                    failures.append(
                        f"[warn]       failed to parse {short_path(input_info.fullname)} "
                        f"from {short_path(other.case_dir)}"
                    )
                    failures.append(
                        f"[debug]         expected rows: {len(exp_info.content)}"
                    )
                    failures.append(f"[debug]         actual rows:   {len(rows)}")

        if failures:
            diagnostics.extend(failures)
            continue

        diagnostics.append(f"[OK]       {cand_name} is a valid reference candidate")
        return candidate, diagnostics

    raise click.ClickException("[FAIL] no valid reference case found.")


def _merge_inputs(dst, cases, verbose, debug, quiet, compact):
    dst_inputs = dst / "inputs"
    merged = {}
    logs = []

    log(
        f"starting merge_inputs with {len(cases)} cases",
        level="debug",
        indent=2,
        quiet=quiet,
        verbose=verbose,
        debug=debug,
        compact=compact,
    )

    for case in cases:
        for inp in case.data.load_inputs():
            name = Path(inp.fullname).name
            content = inp.content

            log(
                f"existing names: {list(merged.keys())}",
                level="debug",
                indent=4,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

            if name not in merged:
                merged[name] = content
                logs.append(f"[OK]     {name} — added")
                continue

            if merged[name] == content:
                logs.append(f"[OK]     {name} — identical, kept")
                continue

            log(
                f"collision detected: {name} already exists",
                level="debug",
                indent=4,
                quiet=quiet,
                verbose=verbose,
                debug=debug,
                compact=compact,
            )

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


def _write_expected_results(
    dst, merged_inputs, template, verbose, debug, quiet, compact
):
    out_dir = dst / "expected_results"
    written = []

    for inp_path in merged_inputs:
        sample = inp_path.read_text()
        rows = parse_textfsm_to_dicts(template, sample)

        log(
            f"parsed rows preview: {rows[:2]}",
            level="debug",
            indent=6,
            quiet=quiet,
            verbose=verbose,
            debug=debug,
            compact=compact,
        )

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
            compact=compact,
        )

    return written
