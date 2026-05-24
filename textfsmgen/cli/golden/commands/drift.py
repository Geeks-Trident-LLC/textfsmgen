from __future__ import annotations

from pathlib import Path

from ..core.utils import catch_path_errors
from ..core.golden_case import GoldenCase


@catch_path_errors
def drift(case_path: Path) -> int:
    """
    Detect drift for a single golden test case.

    Drift applies ONLY to main cases.
    Integration cases never generate golden.hash and therefore
    cannot participate in drift detection.

    Returns:
        0 on success (no drift or integration case)
        1 on drift or error
    """

    case = GoldenCase.from_path(case_path)
    loader = case.data

    # --------------------------------------------------------------
    # Integration cases do NOT support drift
    # --------------------------------------------------------------
    if not case.is_main():
        print(f"[INFO] Drift check skipped for integration case '{case_path.name}'.")
        return 0

    # --------------------------------------------------------------
    # Main case: must have golden.hash
    # --------------------------------------------------------------
    try:
        stored_hash = loader.load_golden_hash()
    except FileNotFoundError:
        print(f"[FAIL]: No golden.hash found for main case '{case_path.name}'.")
        print("        Run 'regen' to generate a baseline before checking drift.")
        return 1
    except Exception as exc:
        print(f"[FAIL]: Failed reading golden.hash\n  {exc}")
        return 1

    # --------------------------------------------------------------
    # Compute current hash of authoritative files
    # --------------------------------------------------------------
    try:
        current_hash = loader.compute_golden_hash()
    except Exception as exc:
        print(f"[FAIL]: Failed computing current golden hash\n  {exc}")
        return 1

    # --------------------------------------------------------------
    # Compare
    # --------------------------------------------------------------
    if current_hash == stored_hash:
        print(f"[OK] No drift detected in '{case_path.name}'.")
        return 0

    # Drift detected
    print(f"[FAIL] Golden files drift detected in '{case_path.name}'.")
    print("       The authoritative files have changed since last regen.")
    return 1
