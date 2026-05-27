from __future__ import annotations


import json
import shutil
from pathlib import Path
import click

from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..core.golden_case import GoldenCase
from ..commands.shared import print_status
from ..cli_decorator import timed_command, validate_sandbox_flags
from ..core.utils import validate_case_path
from .shared import _open_directory


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
        print_status(f"Using sandbox directory: {file.path_name(dst)}", sandbox=True)

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
    for c in cases:
        ok = validate_case_path(c.case_dir)
        if not ok:
            raise click.ClickException(f"Invalid case: {ok}")

        if not c.is_integration():
            raise click.ClickException(
                f"Merge is only supported for integration cases: {file.path_name(c.case_dir)}"
            )

        try:
            c.tested()
        except Exception as e:
            raise click.ClickException(
                f"Case {file.path_name(c.case_dir)} is not tested:\n{e}"
            )

    # Cross‑check all pairs
    for outer in cases:
        for inner in cases:
            if outer is inner:
                continue
            outer.check(inner)

    # ------------------------------------------------------------
    # 3. Find reference template + snippet
    # ------------------------------------------------------------
    reference = _find_reference_case(cases, verbose=verbose)
    ref_loader = reference.data
    ref_template = ref_loader.load_expected().template.content
    ref_snippet = ref_loader.load_expected().snippet.content

    print_status(
        f"Reference case selected: {file.path_name(reference.case_dir)}",
        ok=True,
    )

    if dry_run:
        print_status("[DRY-RUN] Would create merged case", dryrun=True)
        if summary:
            print_status("Summary not available in dry-run mode.", dryrun=True)
        return 0

    # ------------------------------------------------------------
    # 4. Create dst structure
    # ------------------------------------------------------------
    (dst / "inputs").mkdir(parents=True)
    (dst / "expected").mkdir(parents=True)
    (dst / "expected_results").mkdir(parents=True)

    # ------------------------------------------------------------
    # 5. Merge inputs
    # ------------------------------------------------------------
    merged_inputs = _merge_inputs(dst, cases, verbose=verbose)

    # ------------------------------------------------------------
    # 6. Write reference template + snippet
    # ------------------------------------------------------------
    (dst / "expected" / "textfsm.template").write_text(ref_template)
    (dst / "expected" / "snippet.txt").write_text(ref_snippet)

    # ------------------------------------------------------------
    # 7. Generate expected_results
    # ------------------------------------------------------------
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
        print_status("===== MERGE SUMMARY =====", ok=True)
        print_status(f"Reference case: {file.path_name(reference.case_dir)}", ok=True)
        print_status(f"Inputs merged: {len(merged_inputs)}", ok=True)
        for p in merged_inputs:
            print(f"  - {file.path_name(p)}")
        print_status(f"Expected results: {len(written_results)}", ok=True)
        for p in written_results:
            print(f"  - {file.path_name(p)}")
        print_status("=========================", ok=True)

    # ------------------------------------------------------------
    # 10. Sandbox cleanup
    # ------------------------------------------------------------
    if sandbox:
        print_status("Cleaning up sandbox directory.", sandbox=True)
        shutil.rmtree(dst)
        print_status(
            f"[SUCCESS] sandbox merge completed for {file.path_name(real_dst)}"
        )
        return 0

    if sandbox_keep:
        print_status(f"[SUCCESS] sandbox-keep: preserved {file.path_name(dst)}")
        return 0

    # ------------------------------------------------------------
    # 11. Normal success
    # ------------------------------------------------------------
    print_status(f"[SUCCESS] Merge completed: {file.path_name(dst)}", success=True)

    if open_after:
        _open_directory(dst)

    return 0


# ======================================================================
# INTERNAL HELPERS
# ======================================================================


def _find_reference_case(cases: list[GoldenCase], verbose=False) -> GoldenCase:
    for candidate in cases:
        cand_loader = candidate.data
        cand_template = cand_loader.load_expected().template.content

        all_ok = True

        for other in cases:
            for input_info, exp_info in other.data.load_input_result_pairs():
                rows = parse_textfsm_to_dicts(cand_template, input_info.content)
                if rows != exp_info.content:
                    all_ok = False
                    break
            if not all_ok:
                break

        if all_ok:
            return candidate

    raise click.ClickException(
        "No valid reference case found (no template matches all expected results)."
    )


def _merge_inputs(dst: Path, cases: list[GoldenCase], verbose=False) -> list[Path]:
    dst_inputs = dst / "inputs"
    merged = {}

    for case in cases:
        for inp in case.data.load_inputs():
            name = Path(inp.fullname).name
            content = inp.content

            if name not in merged:
                merged[name] = content
                continue

            if merged[name] == content:
                continue

            base = Path(name).stem
            ext = Path(name).suffix
            counter = 2

            while True:
                new_name = f"{base}_{counter}{ext}"
                if new_name not in merged:
                    merged[new_name] = content
                    break
                counter += 1

    written = []
    for name, content in merged.items():
        out_path = dst_inputs / name
        out_path.write_text(content)
        written.append(out_path)

    return written


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

    return written


# ==============================================================================
#
# from pathlib import Path
# import shutil
# import json
#
# from ..core.golden_case import GoldenCase
# from .quicktest import quicktest
#
#
# def merge(dst: Path, srcs: list[Path], *, author: str, dry_run: bool = False) -> int:
#     """
#     Merge multiple integration cases into a new destination case.
#
#     Workflow:
#       - Ensure all dst, srcs are integration cases
#       - Ensure all srcs share the same builder_type
#       - Ensure all srcs pass quicktest
#       - Create dst structure (real or temp)
#       - Copy all src/inputs into dst/inputs (safe merge)
#       - Invoke golden_case.data.create_merge()
#       - Run quicktest on dst
#       - Clean up dry-run temp directory on success
#     """
#
#     # --------------------------------------------------------------
#     # Resolve paths
#     # --------------------------------------------------------------
#     dst = dst.resolve()
#     srcs = [p.resolve() for p in srcs]
#
#     # --------------------------------------------------------------
#     # Validate all cases are integration
#     # --------------------------------------------------------------
#     for p in [dst] + srcs:
#         case = GoldenCase.from_path(p)
#         if not case.is_integration():
#             print(f"[FAIL] Not an integration case: {p}")
#             return 1
#
#     # --------------------------------------------------------------
#     # Validate all sources share the same builder_type
#     # --------------------------------------------------------------
#     builder_types = set()
#     for src in srcs:
#         manifest = json.loads((src / "manifest.json").read_text())
#         builder_types.add(manifest.get("builder"))
#
#     if len(builder_types) != 1:
#         print(f"[FAIL] Sources have different builder_type values: {builder_types}")
#         return 1
#
#     builder_type = builder_types.pop()
#     print(f"[INFO] builder = {builder_type}")
#
#     # --------------------------------------------------------------
#     # Validate all sources pass quicktest
#     # --------------------------------------------------------------
#     for src in srcs:
#         print(f"[INFO] Validating source: {src}")
#         if quicktest(src, dry_run=False) != 0:
#             print(f"[FAIL] Source case failed quicktest: {src}")
#             return 1
#
#     # --------------------------------------------------------------
#     # Dry-run redirect BEFORE creating anything
#     # --------------------------------------------------------------
#     if dry_run:
#         temp = dst.with_name(dst.name + ".temp")
#         print(f"[DRY-RUN] Using temporary directory: {temp}")
#         dst = temp
#
#     # --------------------------------------------------------------
#     # Create destination directory (real or temp)
#     # --------------------------------------------------------------
#     if dst.exists():
#         print(f"[FAIL] Destination already exists: {dst}")
#         return 1
#
#     print(f"[INFO] Creating destination case: {dst}")
#     (dst / "inputs").mkdir(parents=True)
#     (dst / "expected").mkdir()
#     (dst / "expected_results").mkdir()
#
#     # Write manifest.json
#     manifest = {
#         "builder": builder_type,
#         "parameters": {},
#         "meta": {
#             "author": author,
#             "saved": True,
#             "email": "",
#             "description": "",
#             "notes": "",
#             "schema_version": "1.0",
#         },
#     }
#     (dst / "manifest.json").write_text(json.dumps(manifest, indent=2))
#
#     # --------------------------------------------------------------
#     # Copy inputs from all sources (safe merge)
#     # --------------------------------------------------------------
#     src_cases = []
#     for src in srcs:
#         src_case = GoldenCase.from_path(src)
#         src_cases.append(src_case)
#
#         for inp in src_case.data.load_inputs():
#             name = Path(inp.fullname).name
#             dst_path = dst / "inputs" / name
#
#             if not dst_path.exists():
#                 # No conflict → copy normally
#                 dst_path.write_text(inp.content)
#                 continue
#
#             # Conflict: file exists → compare content
#             existing_content = dst_path.read_text()
#
#             if existing_content == inp.content:
#                 # Same content → skip
#                 print(
#                     f"[INFO] Input '{name}' already exists with identical content. Skipped."
#                 )
#                 continue
#
#             # Different content → generate new unique filename
#             base = Path(name).stem
#             ext = Path(name).suffix
#
#             counter = 2
#             while True:
#                 new_name = f"{base}_{counter}{ext}"
#                 new_path = dst / "inputs" / new_name
#                 if not new_path.exists():
#                     new_path.write_text(inp.content)
#                     print(f"[INFO] Input '{name}' differs. Saved as '{new_name}'.")
#                     break
#                 counter += 1
#
#     # --------------------------------------------------------------
#     # Perform merge
#     # --------------------------------------------------------------
#     dst_case = GoldenCase.from_path(dst)
#     print("[INFO] Creating merged expected artifacts...")
#     is_merged = dst_case.data.create_merge(src_cases)
#     if not is_merged:
#         if dst_case.case_dir.exists():
#             print("[INFO] Cleaning up directory.")
#             shutil.rmtree(dst)
#
#         print("[FAIL] source cases dont have the common case for all cases.")
#         return 1
#
#     # --------------------------------------------------------------
#     # Quicktest on merged case
#     # --------------------------------------------------------------
#     print("[INFO] Running quicktest on merged case...")
#     rc = quicktest(dst, dry_run=False)
#
#     # --------------------------------------------------------------
#     # Dry-run cleanup
#     # --------------------------------------------------------------
#     if dry_run:
#         print("[DRY-RUN] Cleaning up temporary directory.")
#         shutil.rmtree(dst)
#         if rc != 0:
#             print("[DRY-RUN] Merge failed. Temporary directory preserved.")
#
#     return rc
