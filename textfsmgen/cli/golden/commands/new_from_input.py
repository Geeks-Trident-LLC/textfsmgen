from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..core.golden_case import GoldenCase
from .quicktest import quicktest as run_quicktest


def new_from_input(
    case_path: Path,
    inputs_dir: Path,
    *,
    builder: str,
    params: dict | None,
    author: str,
    accept: bool,
    dry_run: bool,
    force: bool,
) -> int:
    """
    Create a new INTEGRATION golden test case from an input folder.

    Rules:
      - <case> MUST be under golden/integration
      - Reject if <case> contains main/
      - If dry-run: create <case>.temp
      - Create expected/, expected_results/
      - Write manifest.json with builder + author + params
      - Load GoldenCase
      - Invoke generate_expected()
      - Run quicktest
      - Cleanup rules:
            dry-run always cleans up
            if quicktest fails and not accept → cleanup
    """

    # --------------------------------------------------------------
    # Validate case path
    # --------------------------------------------------------------
    parts = case_path.parts
    if "main" in parts:
        print("[FAIL] Cannot create a new case under 'main/'.")
        print(
            "       Main cases contain canonical authoritative truth and must be created manually."
        )
        print(
            "       Use an integration path instead, e.g.: tests/golden/integration/<case>"
        )
        return 1

    if "integration" not in parts:
        print("[FAIL] <case> must be under golden/integration/")
        return 1

    # --------------------------------------------------------------
    # Dry-run: redirect to <case>.temp
    # --------------------------------------------------------------
    final_case_path = case_path
    if dry_run:
        final_case_path = case_path.with_name(case_path.name + ".temp")
        print(f"[DRY-RUN] Using temporary directory: {final_case_path}")

    # --------------------------------------------------------------
    # Overwrite handling
    # --------------------------------------------------------------
    if final_case_path.exists():
        if dry_run:
            print(
                f"[DRY-RUN] Temporary directory already exists, removing: {final_case_path}"
            )
            shutil.rmtree(final_case_path)

        else:
            if not force:
                print(f"[FAIL] Case directory already exists: {final_case_path}")
                print("       Use --force to overwrite.")
                return 1

            print(
                f"[INFO] Overwriting existing case directory due to --force: {final_case_path}"
            )
            shutil.rmtree(final_case_path)

    final_case_path.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # Create folders
    # --------------------------------------------------------------
    expected_dir = final_case_path / "expected"
    results_dir = final_case_path / "expected_results"

    expected_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # Write manifest.json
    # --------------------------------------------------------------
    manifest_path = final_case_path / "manifest.json"
    manifest = {
        "builder": builder,
        "parameters": params or {},
        "meta": {
            "author": author,
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    # --------------------------------------------------------------
    # Load GoldenCase
    # --------------------------------------------------------------
    case = GoldenCase.from_path(final_case_path)

    # --------------------------------------------------------------
    # Copy input files into inputs/
    # --------------------------------------------------------------
    inputs_target = final_case_path / "inputs"
    inputs_target.mkdir(exist_ok=True)

    src_files = sorted(Path(inputs_dir).glob("*"))
    if not src_files:
        print("[FAIL] No input files found in input folder.")
        if dry_run:
            shutil.rmtree(final_case_path)
        return 1

    for f in src_files:
        shutil.copy2(f, inputs_target / f.name)

    # --------------------------------------------------------------
    # Generate expected artifacts
    # --------------------------------------------------------------
    print("[INFO] Generating expected artifacts...")
    case.data.generate_expected()

    # --------------------------------------------------------------
    # Run quicktest
    # --------------------------------------------------------------
    print("[INFO] Running quicktest...")
    rc = run_quicktest(final_case_path)

    # --------------------------------------------------------------
    # Handle quicktest result
    # --------------------------------------------------------------
    if rc == 0:
        print("[OK] quicktest passed.")

        # ----------------------------------------------------------
        # List all generated artifacts
        # ----------------------------------------------------------
        print("\n[INFO] Generated artifacts:")

        manifest_file = final_case_path / "manifest.json"
        if manifest_file.exists():
            print(f"  - {manifest_file}")

        expected_dir = final_case_path / "expected"
        if expected_dir.exists():
            for f in sorted(expected_dir.glob("*")):
                print(f"  - {f}")

        results_dir = final_case_path / "expected_results"
        if results_dir.exists():
            for f in sorted(results_dir.glob("*.json")):
                print(f"  - {f}")

        print("")  # spacing

        # ----------------------------------------------------------
        # Cleanup for dry-run
        # ----------------------------------------------------------
        if dry_run:
            print("[DRY-RUN] Cleaning up temporary directory.")
            shutil.rmtree(final_case_path)

        return 0

    # quicktest failed
    print("[FAIL] quicktest failed.")

    if dry_run:
        print("[DRY-RUN] Cleaning up temporary directory.")
        shutil.rmtree(final_case_path)
        return 1

    if not accept:
        print("[INFO] Removing failed case because --accept was not provided.")
        shutil.rmtree(final_case_path)
        return 1

    print(
        "[INFO] Leaving failed case for manual inspection because --accept was provided."
    )
    return 1
