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

import textfsm
import textfsmgen

from textfsmgen import (
    CategoryTemplateBuilder,
    TabularTemplateBuilder,
)

from textfsmgen.libs.generic import DotObject, StatusString
from textfsmgen.libs.common import parse_textfsm_to_dicts


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

    def create_merge(self, source_cases):
        """
        Select a reference case whose template can successfully parse
        all inputs from all source cases. Provide detailed diagnostics
        explaining why each candidate failed.
        """

        diagnostics = []
        ref_candidates = []

        # --------------------------------------------------------------
        # 1. Evaluate each candidate reference case
        # --------------------------------------------------------------
        for case_i in source_cases:
            template_i = case_i.data.load_expected().template.content
            case_name = extract_subpath_after("golden", case_i.case_dir)

            case_ok = True
            non_ref_messages = []

            # Check template_i against all inputs of all cases
            for case_j in source_cases:
                if case_i == case_j:
                    continue

                all_inputs_passed = True
                for input_info, result_info in case_j.data.load_input_result_pairs():
                    rows = parse_textfsm_to_dicts(
                        template_i,
                        input_info.content
                    )
                    expected_result = result_info.content
                    if rows != expected_result or (rows == expected_result and not rows):
                        all_inputs_passed = all_inputs_passed and False
                        case_ok = case_ok and False

                if not all_inputs_passed:
                    case_j_name = extract_subpath_after("golden", case_j.case_dir)
                    non_ref_messages.append(
                        f"Template from {case_name} failed to parse "
                        f"all inputs from case {case_j_name}."
                    )
            if case_ok:
                ref_candidates.append(case_i)
                diagnostics.append(
                    f"[OK] Case '{case_name}' is a valid reference candidate."
                )
            else:
                diagnostics.append(
                    f"[INFO] Case '{case_name}' is NOT a valid reference candidate:\n"
                    + "\n".join(f"    - {err}" for err in non_ref_messages)
                )
        # --------------------------------------------------------------
        # 2. No valid reference case
        # --------------------------------------------------------------
        if not ref_candidates:
            print("[MERGE] No valid reference case found.")
            print("\n".join(diagnostics))
            return False

        # --------------------------------------------------------------
        # 3. Pick the first valid reference case
        # --------------------------------------------------------------
        ref_case = ref_candidates[0]
        ref_name = extract_subpath_after("golden", ref_case.case_dir)

        print("[MERGE] Reference case selected:", ref_name)
        print("\n".join(diagnostics))

        ref_expected = ref_case.data.load_expected()
        ref_manifest = ref_case.data.load_manifest()

        # --------------------------------------------------------------
        # 4. Copy parameters from reference manifest
        # --------------------------------------------------------------
        manifest = self.load_manifest()
        manifest["parameters"] = ref_manifest.get("parameters", {}).copy()
        self.write_manifest(manifest=manifest)

        # --------------------------------------------------------------
        # 5. Write snippet + template from reference
        # --------------------------------------------------------------
        snippet_path = self.case_dir / "expected" / "snippet.txt"
        snippet_path.write_text(ref_expected.snippet.content, encoding="utf-8")

        template = ref_expected.template.content
        template_path = self.case_dir / "expected" / "textfsm.template"
        template_path.write_text(template, encoding="utf-8")

        # --------------------------------------------------------------
        # 6. Generate expected_results for all inputs in merged case
        # --------------------------------------------------------------
        for input_info in self.load_inputs():
            in_path = Path(input_info.fullname)
            out_path = self.case_dir / "expected_results" / f"{in_path.stem}_result.json"

            rows = parse_textfsm_to_dicts(template, input_info.content)
            out_path.write_text(
                json.dumps(rows, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        return True

    def generate_expected(self):
        """
        Generate expected snippet, template, and expected_results/*.json
        for an integration case.

        Rules:
          - First input defines snippet + template + reference columns
          - All subsequent inputs must produce rows with identical columns
          - Write:
                expected/snippet.txt
                expected/textfsm.template
                expected_results/<input>_result.json
        """
        manifest = self.load_manifest()
        builder_name = manifest.get("builder")

        snippet = ""
        template = ""
        reference_rows = None
        groups = []  # list of (input_file, rows)

        # --------------------------------------------------------------
        # Process each input
        # --------------------------------------------------------------
        for input_info in self.load_inputs():
            sample = input_info.content
            in_file = input_info.fullname

            # Build from sample
            builder = self.build(sample)
            if not builder:
                return StatusString(
                    f"Cannot create {builder_name} builder from input {in_file}",
                    status=False,
                )

            # ----------------------------------------------------------
            # First input: establish snippet, template, reference rows
            # ----------------------------------------------------------
            if not template:
                snippet = builder.snippet
                template = builder.template

                reference_rows = parse_textfsm_to_dicts(template, sample)
                if not reference_rows:
                    return StatusString(
                        f"No records found after parsing input {in_file}",
                        status=False,
                    )

                groups.append((in_file, reference_rows))
                continue

            # ----------------------------------------------------------
            # Subsequent inputs: must match reference columns
            # ----------------------------------------------------------
            rows = parse_textfsm_to_dicts(template, sample)
            if not rows:
                return StatusString(
                    f"No records found after parsing input {in_file}",
                    status=False,
                )

            # Column consistency check
            if set(rows[0].keys()) != set(reference_rows[0].keys()):
                ref_file = groups[0][0]
                return StatusString(
                    f"Inconsistent columns between:\n"
                    f"  - {ref_file}\n"
                    f"  - {in_file}",
                    status=False,
                )

            groups.append((in_file, rows))

        # --------------------------------------------------------------
        # Write outputs
        # --------------------------------------------------------------
        if not groups:
            return StatusString("No inputs found", status=False)

        expected_dir = self.case_dir / "expected"
        results_dir = self.case_dir / "expected_results"

        expected_dir.mkdir(exist_ok=True)
        results_dir.mkdir(exist_ok=True)

        # snippet
        (expected_dir / "snippet.txt").write_text(snippet, encoding="utf-8")

        # template
        (expected_dir / "textfsm.template").write_text(template,
                                                       encoding="utf-8")

        # expected_results/*.json
        for in_file, rows in groups:
            in_path = Path(in_file)
            out_path = results_dir / f"{in_path.stem}_result.json"
            out_path.write_text(
                json.dumps(rows, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return StatusString(status=True)


    def build(self, sample):
        """
        Instantiate the correct builder (category/tabular)
        using manifest.json and sample input.
        Returns builder with .snippet and .template.
        """
        manifest = self.load_manifest()
        builder_name = manifest.get("builder")
        params = manifest.get("parameters", {})

        # Instantiate correct builder
        if builder_name == "category":
            builder = CategoryTemplateBuilder(user_data=sample, **params)

        elif builder_name == "tabular":
            builder = TabularTemplateBuilder(user_data=sample, **params)

        else:
            raise ValueError(f"Unknown builder type: {builder_name}")

        return builder

    def load_canonical(self, root=""):
        canonical_path = self.case_dir / "canonical"
        canonical_info = DotObject(
            sample=load_file_info(canonical_path / "sample.txt", root=root),
            snippet=load_file_info(canonical_path / "snippet.txt", root=root),
            template=load_file_info(canonical_path / "textfsm.template", root=root),
            result=load_file_info(canonical_path / "result.json", root=root),
        )
        return canonical_info

    def load_expected(self, root=""):
        expected_path = self.case_dir / "expected"
        expected_info = DotObject(
            snippet=load_file_info(expected_path / "snippet.txt", root=root),
            template=load_file_info(expected_path / "textfsm.template", root=root),
        )
        return expected_info

    def load_inputs(self, root=""):
        """
        Yield dictionaries containing input file names (relative to 'golden/')
        and their raw text content.
        """
        inputs_dir = self.case_dir / "inputs"

        for path in inputs_dir.glob("*.txt"):
            yield load_file_info(path, root=root)

    def load_expected_results(self, root=""):
        """
        Yield dictionaries containing expected result file names (relative to 'golden/')
        and their parsed JSON content.
        """
        results_dir = self.case_dir / "expected_results"

        for path in results_dir.glob("*.json"):
            yield load_file_info(path, root=root)

    def load_input_result_pairs(self, root=""):
        """
        Yield (input_info, result_info) tuples where each input file is paired
        with its corresponding expected result JSON file.
        """
        inputs_dir = self.case_dir / "inputs"
        results_dir = self.case_dir / "expected_results"

        for input_path in inputs_dir.glob("*.txt"):
            result_path = results_dir / f"{input_path.stem}_result.json"
            input_info = load_file_info(input_path, root=root)
            result_info = load_file_info(result_path, root=root)

            yield input_info, result_info

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

    def write_manifest(self, manifest: Dict[str, Any]) -> None:
        manifest_path = self.case_dir / MANIFEST_FILENAME
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(manifest, ensure_ascii=False, indent=2))

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

        # Determine authoritative directories
        if self.is_main_case():
            dirs = ["canonical", "inputs", "expected_results"]
        else:
            dirs = ["expected", "inputs", "expected_results"]

        # Include manifest.json if present
        manifest_path = self.case_dir / MANIFEST_FILENAME
        if manifest_path.is_file():
            hasher.update(b"manifest.json\n")
            hasher.update(manifest_path.read_bytes())
            hasher.update(b"\n")

        # Hash authoritative directories
        for d in dirs:
            dir_path = self.case_dir / d
            if not dir_path.exists():
                continue

            for file in sorted(dir_path.rglob("*")):
                if file.is_file():
                    rel = file.relative_to(self.case_dir).as_posix().encode()
                    hasher.update(rel + b"\n")
                    hasher.update(file.read_bytes())
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

    def load_golden_hash(self) -> str:
        hash_path = self.case_dir / HASH_FILENAME
        return hash_path.read_text(encoding="utf-8").strip()

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
        except Exception:   # noqa
            return "unknown"


def extract_subpath_after(root: str, full_path: Path) -> Path:
    """
    Return the portion of `full_path` that appears after the first occurrence
    of the directory name `root`.

    Example:
        full_path = /a/b/golden/network/ospf/case1
        root      = "golden"
        result    = network/ospf/case1
    """
    if not isinstance(full_path, Path):
        full_path = Path(full_path)
    resolved = full_path.resolve()
    parts = resolved.parts

    try:
        index = parts.index(root)
    except ValueError:
        raise ValueError(f"'{root}' not found in path: {resolved}")

    return Path(*parts[index + 1:])


def load_file_info(path: Path, root: str = ""):
    """
    Return a DotObject describing a file, including:
      - name:     relative name (after `root`, if provided)
      - fullname: absolute path as string
      - content:  parsed JSON or raw text

    JSON files are automatically parsed; all others are returned as text.
    """
    resolved = path.resolve()
    fullname = str(resolved)

    # Compute relative name if root is provided
    if root:
        rel_name = str(extract_subpath_after(root, resolved))
    else:
        rel_name = str(resolved)

    # Parse JSON files
    if resolved.suffix == ".json":
        content = json.loads(resolved.read_text(encoding="utf-8"))
    else:
        content = resolved.read_text(encoding="utf-8")

    return DotObject(
        name=rel_name,
        fullname=fullname,
        content=content,
    )
