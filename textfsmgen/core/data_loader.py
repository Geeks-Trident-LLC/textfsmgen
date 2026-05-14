import hashlib
import json
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from typing import List, Optional

import textfsm

import textfsmgen

from textfsmgen import (
    TabularTemplateBuilder,
    CategoryTemplateBuilder,
    parse_textfsm_to_dicts
)


from textfsmgen.exceptions import raise_runtime_error


def write_text_atomic(path, text):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_json_atomic(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


@dataclass
class DirInfo:
    parent: str
    name: str
    children: List[str]


@dataclass(frozen=True)
class GoldenCaseInfo:
    kind: str
    name: str
    path: Path


class DataLoader:
    def __init__(self, test_case):
        self.file_path = self.validate_test_case(test_case)
        self.kind = self.file_path.parent.name
        self.test_case = test_case

        self.case_info = GoldenCaseInfo(
            kind=self.kind,
            name=test_case,
            path=self.file_path,
        )

        self.manifest_path = self.file_path / "manifest.json"
        self.inputs_path = self.file_path / "inputs"
        self.expected_results_path = self.file_path / "expected_results"

        self.parameters = {}
        self.builder_type = ""
        self.meta = None

        self.canonical_sample = ""
        self.canonical_snippet = ""
        self.canonical_template = ""
        self.canonical_result = []

        self.expected_snippet = ""
        self.expected_template = ""

        self.load_manifest()
        self.load_canonical()
        self.load_expected()

    @classmethod
    def validate_test_case(cls, test_case: str) -> Path:
        """
        Validate a test case folder.

        Rules:
        - Accept full paths as-is.
        - Resolve relative paths against the current working directory.
        - Folder must exist and be a directory.
        - Folder must contain either:
            canonical/ + required files
            OR
            expected/  + required files
        """

        raw = Path(test_case)

        # Resolve full vs relative path
        folder = raw if raw.is_absolute() else Path.cwd() / raw
        folder = folder.resolve()

        # Must exist and be a directory
        if not folder.exists() or not folder.is_dir():
            raise_runtime_error(
                obj="InvalidTestCaseStructure",
                msg=(
                    f"Test case not found or not a directory: {test_case}\n"
                    f"Resolved path: {folder}"
                ),
            )

        # --- Helper to validate required files ---
        def check_required(required_paths):
            missing = [str(p.relative_to(folder)) for p in required_paths if
                       not p.exists()]
            if missing:
                raise_runtime_error(
                    obj="InvalidTestCaseStructure",
                    msg=(
                        f"Invalid test case: {test_case}; "
                        f"missing required files: {', '.join(missing)}"
                    ),
                )

        # Canonical-style case
        canonical_dir = folder / "canonical"
        if canonical_dir.exists():
            required = [
                folder / "manifest.json",
                canonical_dir / "sample.txt",
                canonical_dir / "snippet.txt",
                canonical_dir / "textfsm.template",
                canonical_dir / "result.json",
                folder / "inputs",
                folder / "expected_results",
            ]
            check_required(required)
            return folder

        # Expected-style case
        expected_dir = folder / "expected"
        if expected_dir.exists():
            required = [
                folder / "manifest.json",
                expected_dir / "snippet.txt",
                expected_dir / "textfsm.template",
                folder / "inputs",
                folder / "expected_results",
            ]
            check_required(required)
            return folder

        # Neither canonical/ nor expected/
        raise_runtime_error(
            obj="InvalidTestCaseStructure",
            msg=(
                f"Invalid test case: {test_case}; "
                f"expected either 'canonical/' or 'expected/' folder"
            ),
        )
        return None

    @classmethod
    def validate_file_path(cls, file_path, prefix=""):
        if file_path.exists():
            return
        raise ValueError(
            f"{prefix} {file_path!r} does not exist.  Cannot continue.".strip()
        )


    def load_manifest(self):
        result = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.builder_type = result["builder"].lower().strip()
        self.parameters = result["parameters"]
        self.meta = result["meta"]

    def load_canonical(self):
        if self.kind != "main":
            return

        sample_path = self.file_path / "canonical" / "sample.txt"
        self.validate_file_path(sample_path, prefix="Canonical sample file")
        self.canonical_sample = sample_path.read_text(encoding="utf-8")

        snippet_path = self.file_path / "canonical" / "snippet.txt"
        self.validate_file_path(snippet_path, prefix="Canonical snippet file")
        self.canonical_snippet = snippet_path.read_text(encoding="utf-8")

        template_path = self.file_path / "canonical" / "textfsm.template"
        self.validate_file_path(template_path, prefix="Canonical TextFSM template file")
        self.canonical_template = template_path.read_text(encoding="utf-8")

        result_path = self.file_path / "canonical" / "result.json"
        self.validate_file_path(result_path, prefix="Canonical result file")

        self.canonical_result = json.loads(result_path.read_text(encoding="utf-8")) or []

    def load_expected(self):
        if self.kind == "main":
            return

        snippet_path = self.file_path / "expected" / "snippet.txt"
        self.validate_file_path(snippet_path, prefix="Expected snippet file")
        self.expected_snippet = snippet_path.read_text(encoding="utf-8")

        template_path = self.file_path / "expected" / "textfsm.template"
        self.validate_file_path(template_path, prefix="Expected TextFSM template file")
        self.expected_template = template_path.read_text(encoding="utf-8")

    def get_input_and_expected_result(self):
        for input_path in self.inputs_path.glob("*"):
            input_filename = str(input_path)
            basename = input_path.stem
            exp_result_path = self.expected_results_path / f"{basename}_result.json"
            exp_result_filename = str(exp_result_path)

            input_sample = input_path.read_text(encoding="utf-8")
            exp_result = json.loads(exp_result_path.read_text(encoding="utf-8"))
            input_info = {"filename": input_filename, "data": input_sample}
            result_info = {"filename": exp_result_filename, "data": exp_result}
            yield input_info, result_info

    def get_builder(self):
        mapping = {
            "tabular": TabularTemplateBuilder,
            "category": CategoryTemplateBuilder,
        }

        if self.builder_type not in mapping:
            raise ValueError(f"Unknown builder type: {self.builder_type}")

        return mapping[self.builder_type]

    def generate_meta(self):

        # Only write meta when explicitly allowed
        if (
                not os.getenv("GOLDEN_WRITE_META") and
                not os.getenv("GOLDEN_REGEN")
        ):
            return

        if self.kind != "main":
            return

        author = self.meta.get("author", "")
        email = self.meta.get("email", "")
        description = self.meta.get("description", "")
        notes = self.meta.get("notes", "")
        schema_version = self.meta.get("schema_version", "1.0")

        if not author:
            raise ValueError("Author name is required to generate metadata.")

        file_path = self.file_path / "meta.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        approved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            git_commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"])
                .decode("utf-8")
                .strip()
            )
        except Exception:  # noqa
            git_commit = None

        meta = {
            "schema_version": schema_version,
            "approved_by": author,
            "approved_at": approved_at,
            "description": description,
            "email": email,
            "notes": notes,
            "textfsmgen_version": textfsmgen.__version__,
            "textfsm_version": textfsm.__version__,
            "python_version": platform.python_version(),
            "operating_system": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "git_commit": git_commit,
        }

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def regenerate(self):
        """
        Regenerate golden data for this test case.

        Behavior:
        - For 'main' cases:
            * Rebuild canonical result.json (parsed rows from canonical_template + canonical_sample)
        - For 'integration' cases:
            * Rebuild expected_results/*.json (parsed rows from expected_template + inputs)
        - For both kinds:
            * Rewrite meta.json
            * Rewrite golden.hash
        """

        # Only regenerate when explicitly requested
        if not os.getenv("GOLDEN_REGEN"):
            return

        # -----------------------------
        # 1. MAIN CASE: regenerate canonical result.json
        # -----------------------------
        if self.kind == "main":
            # Use authoritative canonical_template + canonical_sample
            rows = parse_textfsm_to_dicts(self.canonical_template,
                                          self.canonical_sample)
            write_json_atomic(
                self.file_path / "canonical" / "result.json",
                rows
            )
            # Use authoritative canonical_template + each input
            for input_sample_info, expected_result_info in self.get_input_and_expected_result():
                input_sample = input_sample_info["data"]
                out_path = expected_result_info["filename"]

                rows = parse_textfsm_to_dicts(self.canonical_template, input_sample)
                write_json_atomic(out_path, rows)

        # -----------------------------
        # 2. INTEGRATION CASE: regenerate expected_results/*.json
        # -----------------------------
        elif self.kind == "integration":
            # Use authoritative expected_template + each input
            for input_sample_info, expected_result_info in self.get_input_and_expected_result():
                input_sample = input_sample_info["data"]
                out_path = expected_result_info["filename"]

                rows = parse_textfsm_to_dicts(self.expected_template,
                                              input_sample)
                write_json_atomic(out_path, rows)

        # -----------------------------
        # 3. Rewrite meta.json
        # -----------------------------
        self.generate_meta()

        # -----------------------------
        # 4. Rewrite golden.hash
        # -----------------------------
        files = self.get_all_golden_files()
        current_hash = compute_hash_for_files(files)
        self.write_hash(current_hash)

    def get_all_golden_files(self):
        files = [
            self.manifest_path,
            # meta.json intentionally excluded from hashing
            # self.file_path / "meta.json",
        ]

        if self.kind == "main":
            files += [
                self.file_path / "canonical" / "snippet.txt",
                self.file_path / "canonical" / "textfsm.template",
                self.file_path / "canonical" / "result.json",
            ]
        else:
            files += [
                self.file_path / "expected" / "snippet.txt",
                self.file_path / "expected" / "textfsm.template",
            ]

        for input_path in self.inputs_path.glob("*"):
            basename = input_path.stem
            files.append(self.expected_results_path / f"{basename}_result.json")

        return files

    def get_hash_file_path(self):
        return self.file_path / "golden.hash"

    def load_stored_hash(self):
        path = self.get_hash_file_path()
        if not path.exists():
            return None
        return path.read_text().strip()

    def write_hash(self, value):
        path = self.get_hash_file_path()
        path.write_text(value, encoding="utf-8")

    def check_drift(self):
        if os.getenv("GOLDEN_REGEN"):
            return  # skip drift check during regeneration

        files = self.get_all_golden_files()
        current_hash = compute_hash_for_files(files)
        stored_hash = self.load_stored_hash()

        if stored_hash is None:
            raise AssertionError(
                f"Golden hash file missing for {self.test_case}. "
                f"Run: pytest --regen-golden"
            )

        if current_hash != stored_hash:
            raise AssertionError(
                f"Golden files drift detected in {self.test_case}.\n"
                f"Run: pytest --regen-golden"
            )


def is_identical_templates(template1, template2):
    # --------------------------------------------------------------------------
    def extract_template(template):
        parts = []
        started = False
        for line in template.splitlines():
            if started:
                parts.append(line)
                continue

            if line.startswith("Value "):
                started = True
                parts.append(line)
        return "\n".join(parts)
    # --------------------------------------------------------------------------
    normalized_template1 = extract_template(template1)
    normalized_template2 = extract_template(template2)
    return normalized_template1 == normalized_template2 and normalized_template1.strip()


def is_identical_snippet(snippet1, snippet2):
    return snippet1.strip() and snippet1.strip() == snippet2.strip()


def compute_hash_for_files(paths):
    h = hashlib.sha256()
    for path in sorted(paths):
        p = Path(path)
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()
