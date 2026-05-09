"""
GoldenCase: High-level behavior for a single golden test case.

This class defines the semantics of:
    - run()
    - regen()

It delegates all file I/O to DataLoader and enforces the rules:

MAIN CASE:
    run()   → write meta.json + golden.hash
    regen() → write meta.json + golden.hash

INTEGRATION CASE:
    run()   → write nothing
    regen() → write meta.json + golden.hash

NEVER write inside:
    canonical/
    expected/
    expected_results/
    inputs/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .data_loader import DataLoader


@dataclass
class GoldenCase:
    """
    Represents a single golden test case.

    This class is intentionally thin. It delegates all metadata and hashing
    logic to DataLoader and only defines the high-level behavior for run()
    and regen().
    """

    case_dir: Path
    data: DataLoader

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    @classmethod
    def from_path(cls, case_path: str | Path) -> "GoldenCase":
        case_dir = Path(case_path).resolve()
        return cls(case_dir=case_dir, data=DataLoader(case_dir))

    # ------------------------------------------------------------------
    # Case type helpers
    # ------------------------------------------------------------------
    def is_main(self) -> bool:
        return self.data.is_main_case()

    def is_integration(self) -> bool:
        return self.data.is_integration_case()

    # ------------------------------------------------------------------
    # RUN behavior
    # ------------------------------------------------------------------
    def run(self) -> None:
        """
        Execute a normal test run for this case.

        MAIN:
            Write meta.json + golden.hash

        INTEGRATION:
            Write nothing

        NEVER write inside canonical/, expected/, expected_results/, inputs/
        """
        if self.is_main():
            self.data.write_meta()
            self.data.write_golden_hash()
        else:
            # Integration run is strictly read-only
            return

    # ------------------------------------------------------------------
    # REGEN behavior
    # ------------------------------------------------------------------
    def regen(self) -> None:
        """
        Execute a regen for this case.

        MAIN:
            Write meta.json + golden.hash

        INTEGRATION:
            Write meta.json + golden.hash

        NEVER write inside canonical/, expected/, expected_results/, inputs/
        """
        self.data.write_meta()
        self.data.write_golden_hash()
