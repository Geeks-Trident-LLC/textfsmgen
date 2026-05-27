from __future__ import annotations

import json
import shutil
from pathlib import Path
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..core.golden_case import GoldenCase
from ..cli_decorator import timed_command, validate_sandbox_flags
from ..core.utils import validate_case_path
from .shared import _open_directory


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
@click.option("--author", help="Set author metadata for the merged case.")
@click.option(
    "--open-after",
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
    author=None,
    open_after=False,
):
    # ------------------------------------------------------------
    # 0. Resolve sandbox destination
    # ------------------------------------------------------------
    real_dst = dst
    if sandbox or sandbox_keep:
        dst = dst.with_name(dst.name + ".temp")
        click.echo(f"[sandbox] Using sandbox directory: {file.path_name(dst)}")

        if dst.exists() and not force:
            raise click.ClickException(
                f"Sandbox directory {file.path_name(dst)} already exists. Use --force to overwrite."
            )

        if dst.exists():
            shutil.rmtree(dst)

    # ------------------------------------------------------------
    # 1. dst must not exist (normal mode)
    # ------------------------------------------------------------
    if not (sandbox or sandbox_keep) and dst.exists():
        raise click.ClickException(f"Destination already exists: {file.path_name(dst)}")

    if not src_paths:
        raise click.ClickException("No source cases provided.")

    # Load GoldenCase objects
    cases = [GoldenCase.from_path(p) for p in src_paths]

    # ------------------------------------------------------------
    # 2. Validate all cases
    # ------------------------------------------------------------
    if verbose:
        click.echo("[OK] builder = " + cases[0].data.load_manifest().get("builder", ""))

    for c in cases:
        if verbose:
            click.echo(f"[INFO] validating source: {file.path_name(c.case_dir)}")

        ok = validate_case_path(c.case_dir)
        if not ok:
            raise click.ClickException(f"[FAIL] {ok}")

        if not c.is_integration():
            raise click.ClickException(
                f"[FAIL] merge is only supported for integration cases: {file.path_name(c.case_dir)}"
            )

        try:
            c.tested()
        except Exception as e:
            raise click.ClickException(
                f"[FAIL] case {file.path_name(c.case_dir)} is not tested:\n{e}"
            )

        if verbose:
            click.echo(f"[OK] {file.path_name(c.case_dir)} — tested and compatible")

    # Cross‑check all pairs
    for outer in cases:
        for inner in cases:
            if outer is inner:
                continue
            outer.check(inner)

    # ------------------------------------------------------------
    # 3. Find reference template + snippet
    # ------------------------------------------------------------
    if verbose:
        click.echo("[INFO] evaluating reference candidates...")

    reference, diagnostics = _find_reference_case(cases, verbose=verbose)

    for diag in diagnostics:
        print(diag)

    click.echo(
        f"[OK] Reference case selected: {file.path_name(reference.case_dir)}",
    )

    ref_loader = reference.data
    ref_template = ref_loader.load_expected().template.content
    ref_snippet = ref_loader.load_expected().snippet.content

    # ------------------------------------------------------------
    # DRY-RUN: stop here
    # ------------------------------------------------------------
    if dry_run:
        click.echo("[DRY-RUN] merge simulation completed.")
        return 0

    # ------------------------------------------------------------
    # 4. Create dst structure
    # ------------------------------------------------------------
    if verbose:
        click.echo(f"[INFO] creating destination case: {file.path_name(dst)}")

    (dst / "inputs").mkdir(parents=True)
    (dst / "expected").mkdir(parents=True)
    (dst / "expected_results").mkdir(parents=True)

    # ------------------------------------------------------------
    # 5. Merge inputs
    # ------------------------------------------------------------
    if verbose:
        click.echo("[INFO] merging inputs...")

    merged_inputs, rename_logs = _merge_inputs(dst, cases, verbose=verbose)

    for log in rename_logs:
        print(log)

    # ------------------------------------------------------------
    # 6. Write reference template + snippet
    # ------------------------------------------------------------
    if verbose:
        click.echo("[INFO] writing template and snippet...")

    (dst / "expected" / "textfsm.template").write_text(ref_template)
    (dst / "expected" / "snippet.txt").write_text(ref_snippet)

    # ------------------------------------------------------------
    # 7. Generate expected_results
    # ------------------------------------------------------------
    if verbose:
        click.echo("[INFO] generating expected_results...")

    written_results = _write_expected_results(
        dst, merged_inputs, ref_template, verbose=verbose
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
    if summary:
        click.echo("[INFO] ===== MERGE SUMMARY =====")
        click.echo(f"[INFO] reference case: {file.path_name(reference.case_dir)}")
        click.echo(f"[INFO] inputs merged: {len(merged_inputs)}")
        for p in merged_inputs:
            print(f"  - {file.path_name(p)}")
        click.echo(f"[INFO] expected results: {len(written_results)}")
        for p in written_results:
            print(f"  - {file.path_name(p)}")
        click.echo("[INFO] =========================")

    # ------------------------------------------------------------
    # 10. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        click.echo("[sandbox] cleaning up sandbox directory.")
        shutil.rmtree(dst)
        click.echo(f"[SUCCESS] sandbox merge completed for {file.path_name(real_dst)}")
        return 0

    if sandbox_keep:
        click.echo(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return 0

    # ------------------------------------------------------------
    # 11. Normal success
    # ------------------------------------------------------------
    click.echo(f"[SUCCESS] merge completed: {file.path_name(dst)}")

    if open_after:
        _open_directory(dst)

    return 0


# ======================================================================
# INTERNAL HELPERS
# ======================================================================


def _find_reference_case(cases: list[GoldenCase], verbose=False):
    diagnostics = []

    for candidate in cases:
        cand_name = file.path_name(candidate.case_dir)
        if verbose:
            diagnostics.append(f"[INFO]   trying: {cand_name}")

        cand_loader = candidate.data
        cand_template = cand_loader.load_expected().template.content

        failures = []

        for other in cases:
            for input_info, exp_info in other.data.load_input_result_pairs():
                rows = parse_textfsm_to_dicts(cand_template, input_info.content)
                if rows != exp_info.content:
                    failures.append(
                        f"[WARN]     - failed to parse {file.path_name(input_info.fullname)} "
                        f"from {file.path_name(other.case_dir)}"
                    )

        if failures:
            diagnostics.extend(failures)
            continue

        diagnostics.append(f"[OK]     {cand_name} is a valid reference candidate")
        return candidate, diagnostics

    raise click.ClickException("[FAIL] no valid reference case found.")


def _merge_inputs(dst: Path, cases: list[GoldenCase], verbose=False):
    dst_inputs = dst / "inputs"
    merged = {}
    logs = []

    for case in cases:
        for inp in case.data.load_inputs():
            name = Path(inp.fullname).name
            content = inp.content

            if name not in merged:
                merged[name] = content
                if verbose:
                    logs.append(f"[OK]   {name} — added")
                continue

            if merged[name] == content:
                if verbose:
                    logs.append(f"[OK]   {name} — identical, kept")
                continue

            # rename
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
    dst: Path, merged_inputs: list[Path], template: str, verbose=False
):
    out_dir = dst / "expected_results"
    written = []

    for inp_path in merged_inputs:
        sample = inp_path.read_text()
        rows = parse_textfsm_to_dicts(template, sample)

        stem = inp_path.stem
        out_path = out_dir / f"{stem}_result.json"
        out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        written.append(out_path)

        if verbose:
            click.echo(
                f"[OK] {file.path_name(inp_path)} → {file.path_name(out_path)} ({len(rows)} rows)",
            )

    return written
