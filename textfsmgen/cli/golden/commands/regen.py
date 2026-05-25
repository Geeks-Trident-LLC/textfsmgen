"""
Implementation of:

    textfsmgen tester regen <case>

Rebuilds *derived artifacts* for a golden test case.

MAIN CASE (derived artifacts):
    - expected_results/*.json
    - meta.json
    - golden.hash

INTEGRATION CASE (derived artifacts):
    - expected/snippet.txt
    - expected/textfsm.template
    - expected_results/*.json

Never modifies authoritative data:
    - canonical/        (ground‑truth snippet/template)
    - inputs/           (user‑authored test inputs)
    - manifest.json     (case identity and configuration)

Sandbox modes (--sandbox, --sandbox-keep):
    - Work inside <case>.temp
    - If <case>.temp exists:
          * require --force to overwrite
    - --sandbox deletes temp on success
    - --sandbox-keep preserves temp always

Normal regen always overwrites derived artifacts; no --force needed.
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil

from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import file

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors
from ..core.data_loader import extract_subpath_after

from ..commands.shared import print_status


@catch_path_errors
def regen(
    case_path: Path,
    *,
    sandbox=False,
    sandbox_keep=False,
    dry_run=False,
    force=False,
    verbose=False,
) -> int:

    case_path = case_path.resolve()
    _v("Resolved case path:", verbose, path=case_path)

    # --------------------------------------------------------------
    # Sandbox modes
    # --------------------------------------------------------------
    if sandbox or sandbox_keep:
        temp_path = case_path.with_name(case_path.name + ".temp")

        print_status(
            f"Using temporary directory: {file.path_name(temp_path)}",
            sandbox=True,
        )
        _v("Preparing sandbox directory", verbose)

        if temp_path.exists():
            _v("Found existing sandbox directory:", verbose, path=temp_path)
            if not force:
                print_status(
                    f"Sandbox directory {file.path_name(temp_path)!r} already exists. "
                    "Use --force to overwrite it.",
                    fail=True,
                    sandbox=True,
                )
                return 1
            _v("Overwriting existing sandbox directory (--force)", verbose)
            shutil.rmtree(temp_path)

        _v("Copying case into sandbox directory", verbose)
        shutil.copytree(case_path, temp_path)

        case_path = temp_path
        case = GoldenCase.from_path(case_path)
        _v("Loaded sandbox case:", verbose, path=case_path)

        rc = regen_main(case, dry_run=dry_run, verbose=verbose) \
            if case.is_main() else \
            regen_integration(case, dry_run=dry_run, verbose=verbose)

        if sandbox:
            if rc == 0:
                print_status("Cleaning up temporary directory.", sandbox=True)
                _v("Removing sandbox directory after successful regen", verbose)
                shutil.rmtree(case_path)
            else:
                print_status(
                    "Regen failed. Temporary directory preserved for inspection.",
                    fail=True,
                )
        else:
            print_status("Preserving temporary directory.", sandbox=True)
            _v("Sandbox-keep: leaving temp directory intact", verbose)

        return rc

    # --------------------------------------------------------------
    # Normal regen
    # --------------------------------------------------------------
    _v("Performing normal regen (no sandbox)", verbose)
    case = GoldenCase.from_path(case_path)
    rc = regen_main(case, dry_run=dry_run, verbose=verbose) \
        if case.is_main() else \
        regen_integration(case, dry_run=dry_run, verbose=verbose)
    return rc


# ---------------------------------------------------------------------------
# MAIN CASE REGEN
# ---------------------------------------------------------------------------
def regen_main(case: GoldenCase, dry_run=False, verbose=False) -> int:
    _v("MAIN case detected", verbose)

    loader = case.data
    canonical = loader.load_canonical()
    _v("Loaded canonical snippet/template", verbose)

    updated = []

    case_name = case.case_dir.name
    # 1. expected_results
    for input_info in loader.load_inputs():
        _v("Processing input:", verbose, path=input_info.fullname, case_name=case_name)

        base = Path(input_info.fullname).stem
        out_path = loader.case_dir / "expected_results" / f"{base}_result.json"

        rows = parse_textfsm_to_dicts(canonical.template.content, input_info.content)
        _v(f"Parsed {len(rows)} rows from input", verbose)

        if not dry_run:
            _v("Writing expected results:", verbose, path=out_path, case_name=case_name)
            out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))

        updated.append(file.path_name(out_path))

    # meta.json
    if not dry_run:
        _v("Writing meta.json", verbose)
        loader.write_meta()
    updated.append(file.path_name(case.case_dir / "meta.json"))

    # golden.hash
    if not dry_run:
        _v("Writing golden.hash", verbose)
        loader.write_golden_hash()
    updated.append(file.path_name(case.case_dir / "golden.hash"))

    _print(case, updated, dry_run=dry_run)
    return 0

# ---------------------------------------------------------------------------
# INTEGRATION CASE REGEN
# ---------------------------------------------------------------------------
def regen_integration(case: GoldenCase, dry_run=False, verbose=False) -> int:
    _v("INTEGRATION case detected:", verbose, path=case.case_dir)

    loader = case.data
    expected = loader.load_expected()

    snippet_written = False
    updated = []

    case_name = case.case_dir.name
    for input_info in loader.load_inputs():
        _v("Processing input:", verbose, path=input_info.fullname, case_name=case_name)

        builder = loader.build(input_info.content)
        if not builder:
            print_status(f"cannot build from input: {input_info.fullname}", fail=True)
            return 1

        if not snippet_written:
            _v("Writing snippet and template", verbose)
            if not dry_run:
                Path(expected.snippet.fullname).write_text(builder.snippet)
                Path(expected.template.fullname).write_text(builder.template)

            updated.append(file.path_name(expected.snippet.fullname))
            updated.append(file.path_name(expected.template.fullname))
            snippet_written = True

        base = Path(input_info.fullname).stem
        out_path = loader.case_dir / "expected_results" / f"{base}_result.json"

        rows = parse_textfsm_to_dicts(builder.template, input_info.content)
        _v(f"Parsed {len(rows)} rows from input", verbose)

        if not dry_run:
            _v("Writing expected results:", verbose, path=out_path, case_name=case_name)
            out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))

        updated.append(file.path_name(out_path))

    _print(case, updated, dry_run=dry_run)
    return 0

# ---------------------------------------------------------------------------
# UTIL
# ---------------------------------------------------------------------------

def _print(case: GoldenCase, files: list[str], dry_run=False) -> None:
    tc_name = extract_subpath_after("golden", case.case_dir)
    message = f"regenerated {file.path_name(tc_name)}"
    if dry_run:
        print_status(message, dryrun=True)
    else:
        print_status(message, success=True)
    for f in files:
        print(f"  - {file.path_name(f)}")


def _v(message: str, verbose: bool, path=None, case_name=""):
    case_name = case_name or "golden"
    if not verbose:
        return
    if not path:
        print_status(message, ok=True)
        return

    path = path if isinstance(path, Path) else Path(path)
    extracted_path = file.path_name(extract_subpath_after(case_name, path))
    print_status(f"{message} {extracted_path}", ok=True)
