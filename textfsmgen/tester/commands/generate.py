from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..core.golden_case import GoldenCase
from .quicktest import quicktest as run_quicktest


def generate(case_path: Path, *, dry_run: bool) -> int:
    """
    Initialize expected artifacts for an existing case that the user manually
    prepared (manifest.json + inputs/).

    Workflow:
      - Case must already exist
      - Manifest must contain valid builder + author
      - Inputs folder must contain files
      - generate_expected()
      - quicktest
      - dry-run: use <case>.temp and delete on success
    """

    # --------------------------------------------------------------
    # Case must exist
    # --------------------------------------------------------------
    if not case_path.exists():
        print(f"[FAIL] Case directory does not exist: {case_path}")
        return 1

    # --------------------------------------------------------------
    # Dry-run: redirect to <case>.temp
    # --------------------------------------------------------------
    final_case_path = case_path
    if dry_run:
        final_case_path = case_path.with_name(case_path.name + ".temp")
        print(f"[DRY-RUN] Using temporary directory: {final_case_path}")

        if final_case_path.exists():
            shutil.rmtree(final_case_path)

        shutil.copytree(case_path, final_case_path)

    # --------------------------------------------------------------
    # Load manifest.json
    # --------------------------------------------------------------
    manifest_path = final_case_path / "manifest.json"
    if not manifest_path.exists():
        print("[FAIL] manifest.json not found in case directory.")
        return 1

    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception:   # noqa
        print("[FAIL] manifest.json is not valid JSON.")
        return 1

    builder = manifest.get("builder")
    author = manifest.get("meta", {}).get("author")

    # --------------------------------------------------------------
    # Validate builder + author
    # --------------------------------------------------------------
    if builder not in ("category", "tabular"):
        print("[FAIL] manifest.json: builder must be 'category' or 'tabular'.")
        return 1

    if not author:
        print("[FAIL] manifest.json: meta.author must be provided.")
        return 1

    # --------------------------------------------------------------
    # Validate inputs folder
    # --------------------------------------------------------------
    inputs_dir = final_case_path / "inputs"
    if not inputs_dir.exists():
        print("[FAIL] inputs/ folder does not exist.")
        return 1

    src_files = sorted(inputs_dir.glob("*"))
    if not src_files:
        print("[FAIL] No input files found in inputs/ folder.")
        return 1

    # --------------------------------------------------------------
    # Load GoldenCase
    # --------------------------------------------------------------
    case = GoldenCase.from_path(final_case_path)

    # --------------------------------------------------------------
    # Generate expected artifacts
    # --------------------------------------------------------------
    print("[INFO] Generating expected artifacts...")
    status = case.data.generate_expected()

    if not status.status:
        print(f"[FAIL] {status.message}")
        if dry_run:
            print("[DRY-RUN] Cleaning up temporary directory.")
            shutil.rmtree(final_case_path)
        return 1

    # --------------------------------------------------------------
    # Run quicktest
    # --------------------------------------------------------------
    print("[INFO] Running quicktest...")
    rc = run_quicktest(final_case_path)

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
