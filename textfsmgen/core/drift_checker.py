# textfsmgen/core/drift_checker.py

import os
import hashlib
from pathlib import Path
from typing import Iterable

from textfsmgen.core.case_loader import CaseLoader


class DriftChecker:
    """
    Computes golden.hash and detects drift.
    """

    def __init__(self, loader: CaseLoader):
        self.loader = loader

    def compute_hash(self) -> str:
        """Compute a deterministic hash over the golden state."""
        h = hashlib.sha256()

        for path in self.iter_files():
            # Use a stable, normalized relative path
            rel = path.relative_to(self.loader.file_path).as_posix()
            h.update(rel.encode("utf-8"))
            h.update(b"\0")

            # Normalize content: text mode, LF newlines
            data = path.read_bytes()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                # Binary fallback: hash raw bytes
                h.update(data)
            else:
                normalized = text.replace("\r\n", "\n")
                h.update(normalized.encode("utf-8"))

            h.update(b"\0")

        return h.hexdigest()

    def hash_path(self) -> Path:
        return self.loader.file_path / "golden.hash"

    def read_stored_hash(self) -> str | None:
        path = self.hash_path()
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8").strip()

    def write_hash(self):
        if self.loader.kind != "main":
            return
        hash_value = self.compute_hash()
        self.hash_path().write_text(hash_value + "\n", encoding="utf-8")

    def check_drift(self) -> None:
        """Compare current golden state with stored hash, or regenerate when GOLDEN_REGEN is set."""
        current = self.compute_hash()
        stored = self.read_stored_hash()

        # Regeneration mode: update hash and return
        if os.getenv("GOLDEN_REGEN"):
            self.write_hash()
            return

        # First run: no stored hash yet
        if stored is None:
            raise AssertionError(
                f"No golden.hash found in {self.loader.file_path}. "
                "Run: pytest --regen-golden"
            )

        if current != stored:
            raise AssertionError(
                f"Golden files drift detected in {self.loader.file_path}.\n"
                f"Stored:  {stored}\n"
                f"Current: {current}\n"
                "Run: pytest --regen-golden"
            )

    def iter_files(self) -> Iterable[Path]:
        """Yield all files that define the golden state in a deterministic order."""
        # 1) manifest.json
        yield self.loader.manifest_path

        # 2) canonical files (main cases only), sorted by relative path
        if self.loader.kind == "main":
            canonical_files = sorted(self.loader.canonical_dir.glob("*"))
            for path in canonical_files:
                if path.is_file():
                    yield path

        # 3) expected results, one per input, sorted by input name
        input_files = sorted(self.loader.inputs_path.glob("*"))
        for inp in input_files:
            if not inp.is_file():
                continue
            expected = self.loader.expected_results_path / f"{inp.stem}_result.json"
            yield expected
