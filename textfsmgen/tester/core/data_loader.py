"""
DataLoader: Responsible for loading metadata, manifest, and generating
meta.json + golden.hash for a golden test case.

STRICT RULES:
- NEVER write inside:
    canonical/
    expected/
    expected_results/
    inputs/

- ONLY write:
    <case>/meta.json
    <case>/golden.hash

- Integration tests:
    run()   → write nothing
    regen() → write meta.json + golden.hash

- Main tests:
    run()   → write meta.json + golden.hash
    regen() → write meta.json + golden.hash
"""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import textfsm  # type: ignore
import textfsmgen  # type: ignore


META_FILENAME = "meta.json"
HASH_FILENAME = "golden.hash"
MANIFEST_FILENAME = "manifest.json"


@dataclass
class DataLoader:
    """
    Load and manage metadata for a single golden test case.

    This class NEVER writes into canonical/, expected/, expected_results/,
    or inputs/. It ONLY writes meta.json and golden.hash at the case root.
    """

    case_dir: Path

    # ----------------------------------------------------------------------
    # Construction
    # ----------------------------------------------------------------------
    @classmethod
    def from_case_path(cls, case_path: str | Path) -> "DataLoader":
        return cls(case_dir=Path(case_path).resolve())

    # ----------------------------------------------------------------------
    # Manifest
    # ----------------------------------------------------------------------
    def load_manifest(self) -> Dict[str, Any]:
        """
        Load manifest.json if present. Missing file returns {}.
        """
        manifest_path = self.case_dir / MANIFEST_FILENAME
        if not manifest_path.is_file():
            return {}
        with manifest_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    # ----------------------------------------------------------------------
    # Case type helpers
    # ----------------------------------------------------------------------
    def is_main_case(self) -> bool:
        """
        A 'main' case is one that has a canonical/ folder.
        """
        return (self.case_dir / "canonical").is_dir()

    def is_integration_case(self) -> bool:
        """
        An 'integration' case is any case that is not main.
        """
        return not self.is_main_case()

    # ----------------------------------------------------------------------
    # Meta generation
    # ----------------------------------------------------------------------
    def generate_meta(
        self,
        *,
        approved_by: str = "",
        approved_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate the meta.json content for this case.

        Rules:
        - schema_version is always "1.0"
        - description/email/notes come from manifest.json
        - approved_by: argument > manifest > ""
        - approved_at: argument > now
        - system/version/git fields always freshly generated
        """
        manifest = self.load_manifest()

        # Extract manifest meta fields
        m = manifest.get("meta", {})
        description = m.get("description", "")
        email = m.get("email", "")
        notes = m.get("notes", "")
        manifest_author = m.get("author", "")

        # approved_by precedence:
        # 1. explicit approved_by argument
        # 2. manifest.meta.author
        approved_by = approved_by or manifest_author

        # approved_at: argument > now
        if approved_at is None:
            approved_at = datetime.now()

        # System info
        operating_system = f"{platform.system()} {platform.release()}"
        machine = platform.machine()
        python_version = platform.python_version()

        # Versions
        textfsmgen_version = getattr(textfsmgen, "__version__", "unknown")
        textfsm_version = getattr(textfsm, "__version__", "unknown")

        # Git commit
        git_commit = self._get_git_commit_hash()

        # Final meta.json structure (ORDER MATTERS)
        meta: Dict[str, Any] = {
            "schema_version": "1.0",
            "approved_by": approved_by,
            "approved_at": approved_at.strftime("%Y-%m-%d %H:%M:%S"),
            "description": description,
            "email": email,
            "notes": notes,
            "textfsmgen_version": textfsmgen_version,
            "textfsm_version": textfsm_version,
            "python_version": python_version,
            "operating_system": operating_system,
            "machine": machine,
            "git_commit": git_commit,
        }

        return meta

    def write_meta(
        self,
        *,
        approved_by: str = "",
        approved_at: Optional[datetime] = None,
    ) -> None:
        """
        Write meta.json at the case root.

        This is the ONLY method that writes meta.json.
        """
        meta = self.generate_meta(approved_by=approved_by, approved_at=approved_at)
        meta_path = self.case_dir / META_FILENAME
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    # ----------------------------------------------------------------------
    # Golden hash
    # ----------------------------------------------------------------------
    def compute_golden_hash(self) -> str:
        """
        Compute a deterministic hash over the golden case.

        IMPORTANT:
        - Does NOT read or write canonical/, inputs/, expected/, expected_results/.
        - Only includes files that define the golden surface:
            manifest.json
            meta.json (if present)
        """
        import hashlib

        hasher = hashlib.sha256()

        # Include manifest.json if present
        manifest_path = self.case_dir / MANIFEST_FILENAME
        if manifest_path.is_file():
            hasher.update(b"manifest.json\n")
            hasher.update(manifest_path.read_bytes())
            hasher.update(b"\n")

        # Include meta.json if present
        meta_path = self.case_dir / META_FILENAME
        if meta_path.is_file():
            hasher.update(b"meta.json\n")
            hasher.update(meta_path.read_bytes())
            hasher.update(b"\n")

        return hasher.hexdigest()

    def write_golden_hash(self) -> None:
        """
        Write golden.hash at the case root.

        This is the ONLY method that writes golden.hash.
        """
        digest = self.compute_golden_hash()
        hash_path = self.case_dir / HASH_FILENAME
        with hash_path.open("w", encoding="utf-8") as f:
            f.write(digest + "\n")

    # ----------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------
    def _get_git_commit_hash(self) -> str:
        """
        Return the current git commit hash, or 'unknown' if not available.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.case_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"
