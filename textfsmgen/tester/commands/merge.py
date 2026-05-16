from __future__ import annotations

from pathlib import Path
import shutil
import json

from ..core.golden_case import GoldenCase
from .quicktest import quicktest


def merge(dst: Path, srcs: list[Path], *, author: str, dry_run: bool = False) -> int:
    """
    Merge multiple integration cases into a new destination case.

    Workflow:
      - Ensure all dst, srcs are integration cases
      - Ensure all srcs share the same builder_type
      - Ensure all srcs pass quicktest
      - Create dst structure (real or temp)
      - Copy all src/inputs into dst/inputs (safe merge)
      - Invoke golden_case.data.create_merge()
      - Run quicktest on dst
      - Clean up dry-run temp directory on success
    """

    # --------------------------------------------------------------
    # Resolve paths
    # --------------------------------------------------------------
    dst = dst.resolve()
    srcs = [p.resolve() for p in srcs]

    # --------------------------------------------------------------
    # Validate all cases are integration
    # --------------------------------------------------------------
    for p in [dst] + srcs:
        case = GoldenCase.from_path(p)
        if not case.is_integration():
            print(f"[FAIL] Not an integration case: {p}")
            return 1

    # --------------------------------------------------------------
    # Validate all sources share the same builder_type
    # --------------------------------------------------------------
    builder_types = set()
    for src in srcs:
        manifest = json.loads((src / "manifest.json").read_text())
        builder_types.add(manifest.get("builder"))

    if len(builder_types) != 1:
        print(f"[FAIL] Sources have different builder_type values: {builder_types}")
        return 1

    builder_type = builder_types.pop()
    print(f"[INFO] builder = {builder_type}")

    # --------------------------------------------------------------
    # Validate all sources pass quicktest
    # --------------------------------------------------------------
    for src in srcs:
        print(f"[INFO] Validating source: {src}")
        if quicktest(src, dry_run=False) != 0:
            print(f"[FAIL] Source case failed quicktest: {src}")
            return 1

    # --------------------------------------------------------------
    # Dry-run redirect BEFORE creating anything
    # --------------------------------------------------------------
    if dry_run:
        temp = dst.with_name(dst.name + ".temp")
        print(f"[DRY-RUN] Using temporary directory: {temp}")
        dst = temp

    # --------------------------------------------------------------
    # Create destination directory (real or temp)
    # --------------------------------------------------------------
    if dst.exists():
        print(f"[FAIL] Destination already exists: {dst}")
        return 1

    print(f"[INFO] Creating destination case: {dst}")
    (dst / "inputs").mkdir(parents=True)
    (dst / "expected").mkdir()
    (dst / "expected_results").mkdir()

    # Write manifest.json
    manifest = {
        "builder": builder_type,
        "parameters": {},
        "meta": {
            "author": author,
            "saved": True,
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }
    (dst / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # --------------------------------------------------------------
    # Copy inputs from all sources (safe merge)
    # --------------------------------------------------------------
    src_cases = []
    for src in srcs:
        src_case = GoldenCase.from_path(src)
        src_cases.append(src_case)

        for inp in src_case.data.load_inputs():
            name = Path(inp.fullname).name
            dst_path = dst / "inputs" / name

            if not dst_path.exists():
                # No conflict → copy normally
                dst_path.write_text(inp.content)
                continue

            # Conflict: file exists → compare content
            existing_content = dst_path.read_text()

            if existing_content == inp.content:
                # Same content → skip
                print(
                    f"[INFO] Input '{name}' already exists with identical content. Skipped."
                )
                continue

            # Different content → generate new unique filename
            base = Path(name).stem
            ext = Path(name).suffix

            counter = 2
            while True:
                new_name = f"{base}_{counter}{ext}"
                new_path = dst / "inputs" / new_name
                if not new_path.exists():
                    new_path.write_text(inp.content)
                    print(f"[INFO] Input '{name}' differs. Saved as '{new_name}'.")
                    break
                counter += 1

    # --------------------------------------------------------------
    # Perform merge
    # --------------------------------------------------------------
    dst_case = GoldenCase.from_path(dst)
    print("[INFO] Creating merged expected artifacts...")
    is_merged = dst_case.data.create_merge(src_cases)
    if not is_merged:
        if dst_case.case_dir.exists():
            print("[INFO] Cleaning up directory.")
            shutil.rmtree(dst)

        print("[FAIL] source cases dont have the common case for all cases.")
        return 1

    # --------------------------------------------------------------
    # Quicktest on merged case
    # --------------------------------------------------------------
    print("[INFO] Running quicktest on merged case...")
    rc = quicktest(dst, dry_run=False)

    # --------------------------------------------------------------
    # Dry-run cleanup
    # --------------------------------------------------------------
    if dry_run:
        print("[DRY-RUN] Cleaning up temporary directory.")
        shutil.rmtree(dst)
        if rc != 0:
            print("[DRY-RUN] Merge failed. Temporary directory preserved.")

    return rc
