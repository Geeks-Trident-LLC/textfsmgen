# textfsmgen/core/drift_checker.py

import os
import hashlib
# from pathlib import Path

from textfsmgen.core.case_loader import CaseLoader


class DriftChecker:
    """
    Computes golden.hash and detects drift.
    """

    def __init__(self, loader: CaseLoader):
        self.loader = loader

    def compute_hash(self) -> str:
        h = hashlib.sha256()
        for path in self.iter_files():
            if path.is_file():
                h.update(path.read_bytes())
        return h.hexdigest()

    def write_hash(self):
        if self.loader.kind != "main":
            return
        hash_value = self.compute_hash()
        (self.loader.file_path / "golden.hash").write_text(hash_value, "utf-8")

    def check_drift(self):
        # --------------------------------------------------------------
        # EXACT behavior from your old DataLoader:
        # Skip drift check during regeneration
        # --------------------------------------------------------------
        if os.getenv("GOLDEN_REGEN"):
            return

        # Only main cases have drift detection
        if self.loader.kind != "main":
            return

        hash_file = self.loader.file_path / "golden.hash"
        if not hash_file.exists():
            raise AssertionError(
                f"Golden hash file missing for {self.loader.name}. "
                f"Run: pytest --regen-golden"
            )

        current = self.compute_hash()
        stored = hash_file.read_text().strip()

        if current != stored:
            raise AssertionError(
                f"Golden files drift detected in {self.loader.name}.\n"
                f"Run: pytest --regen-golden"
            )

    def iter_files(self):
        yield self.loader.manifest_path

        if self.loader.kind == "main":
            yield self.loader.canonical_dir / "sample.txt"
            yield self.loader.canonical_dir / "snippet.txt"
            yield self.loader.canonical_dir / "textfsm.template"
            yield self.loader.canonical_dir / "result.json"

        for inp in self.loader.inputs_path.glob("*"):
            yield self.loader.expected_results_path / f"{inp.stem}_result.json"
