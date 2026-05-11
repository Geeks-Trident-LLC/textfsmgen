from __future__ import annotations

import shutil
from pathlib import Path

from ..core.utils import require_case_dir
from ..core.golden_case import GoldenCase
from ..core.data_loader import DataLoader, extract_subpath_after


def copy_case(
    author: str = "",
    src: Path = None,
    dst: Path = None,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    """
    Copy an existing golden test case into a new case directory.

    Rules:
      - src must be a valid golden test case.
      - dst must be inside a golden/ directory.
      - dst must not exist unless --force is used.

      - Copy authoritative content:
            canonical/  (if main)
            expected/   (if integration)
            inputs/
            expected_results/ (if present)

      - Copy manifest.json, but reset:
            email, notes, description
        and update:
            author=<author>

      - Never copy meta.json or golden.hash.
      - Never generate golden.hash during copy.

      - --dry-run:
            Copy into <dst>.temp, run quicktest, delete temp on success.
            Keep temp on failure.
    """

    # Normalize author=NAME → NAME
    if "=" in author:
        _, author = author.split("=", maxsplit=1)

    # --------------------------------------------------------------
    # Validate source case
    # --------------------------------------------------------------
    try:
        require_case_dir(src)
    except Exception as exc:
        print(
            "[FAIL]: Copy failed because source folder is not a test case folder\n"
            f"  {type(exc).__name__}: {exc}"
        )
        return 1

    # --------------------------------------------------------------
    # Determine actual destination (dry-run uses temp)
    # --------------------------------------------------------------
    real_dst = dst
    temp_dst = dst.with_name(dst.name + ".temp") if dry_run else None
    target_dst = temp_dst if dry_run else real_dst

    # --------------------------------------------------------------
    # Validate destination path
    # --------------------------------------------------------------
    if target_dst.exists():
        if not force:
            print(f"[FAIL]: Destination already exists: {target_dst}")
            return 1
        else:
            print(f"[WARN]: Overwriting existing destination due to --force: {target_dst}")
            shutil.rmtree(target_dst)

    if "golden" not in target_dst.parts:
        print(f"[FAIL]: Destination must be inside a golden/ directory: {target_dst}")
        return 1

    try:
        target_dst.mkdir(parents=True, exist_ok=False)
    except Exception as exc:
        print(f"[FAIL]: Could not create destination directory: {target_dst}\n  {exc}")
        return 1

    # --------------------------------------------------------------
    # Load source case
    # --------------------------------------------------------------
    try:
        source_case = GoldenCase.from_path(src)
        source_loader = DataLoader(src)
    except Exception as exc:
        print(f"[FAIL]: Could not load source case: {src}\n  {exc}")
        return 1

    # --------------------------------------------------------------
    # Copy authoritative directories
    # --------------------------------------------------------------
    try:
        if source_case.is_main():
            _copy_dir_if_exists(src / "canonical", target_dst / "canonical")
        else:
            _copy_dir_if_exists(src / "expected", target_dst / "expected")

        _copy_dir_if_exists(src / "inputs", target_dst / "inputs")
        _copy_dir_if_exists(src / "expected_results", target_dst / "expected_results")

    except Exception as exc:
        print(f"[FAIL]: Failed copying authoritative files\n  {exc}")
        return 1

    # --------------------------------------------------------------
    # Load and rewrite manifest.json
    # --------------------------------------------------------------
    try:
        manifest = source_loader.load_manifest()

        meta = manifest["meta"]
        meta["email"] = ""
        meta["notes"] = ""
        meta["description"] = ""
        meta["author"] = author

        new_loader = DataLoader(target_dst)
        new_loader.write_manifest(manifest)

    except Exception as exc:
        print(f"[FAIL]: Failed writing manifest.json\n  {exc}")
        return 1

    # --------------------------------------------------------------
    # DRY-RUN MODE: run quicktest on <dst>.temp
    # --------------------------------------------------------------
    if dry_run:
        from . import quicktest as cmd_quicktest

        print(f"[INFO]: Running quicktest on dry-run copy: {temp_dst}")
        rc = cmd_quicktest.quicktest(temp_dst)

        if rc == 0:
            src_tc = extract_subpath_after("golden", src)
            dst_tc = extract_subpath_after("golden", real_dst)
            print(f"[OK] Dry-run passed. Safe to copy '{src_tc}' -> '{dst_tc}'.")
            shutil.rmtree(temp_dst)
            return 0
        else:
            print(
                f"[FAIL]: Dry-run failed. Temp case kept for inspection:\n"
                f"  {temp_dst}"
            )
            return 1

    # --------------------------------------------------------------
    # Normal success output
    # --------------------------------------------------------------
    src_tc = extract_subpath_after("golden", src)
    dst_tc = extract_subpath_after("golden", real_dst)

    print(f"[OK] Copied case '{src_tc}' -> '{dst_tc}'")
    print(f"  Author: {author}")
    print(f"  Copied:")
    if source_case.is_main():
        print("    - canonical/")
    else:
        print("    - expected/")
    print("    - inputs/")
    if (src / "expected_results").exists():
        print("    - expected_results/")
    print("  Generated:")
    print("    - manifest.json")

    return 0



# ----------------------------------------------------------------------
# Internal helper
# ----------------------------------------------------------------------
def _copy_dir_if_exists(src: Path, dst: Path) -> None:
    """Copy a directory if it exists."""
    if src.exists():
        shutil.copytree(src, dst)
