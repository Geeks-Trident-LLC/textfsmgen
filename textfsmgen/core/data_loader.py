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


@dataclass
class GoldenPathCache:
    root: Optional[Path] = None
    resolved: bool = False


GOLDEN_PATH = GoldenPathCache()


class DataLoader:
    def __init__(self, kind, test_case):
        self.kind = kind
        self.test_case = test_case

        self.golden_root = self._resolve_golden_root()

        self.case_info = GoldenCaseInfo(
            kind=kind,
            name=test_case,
            path=self.golden_root / kind / test_case,
        )

        self.file_path = self.golden_root / kind / test_case
        self.manifest_path = self.golden_root / kind / test_case / "manifest.json"
        self.inputs_path = self.golden_root / kind / test_case / "inputs"
        self.expected_results_path = self.golden_root / kind / test_case / "expected_results"

        self.parameters = {}
        self.builder_type = ""
        self.meta = None

        self.canonical_sample = ""
        self.canonical_snippet = ""
        self.canonical_template = ""
        self.canonical_result = []

        self.expected_snippet = ""
        self.expected_template = ""

        self.validate()
        self.load_manifest()
        self.load_canonical()
        self.load_expected()

    def _resolve_golden_root(self) -> Path: # noqa
        """
        Resolve and cache the golden root directory.
        Raises RuntimeError if not found.
        """
        # Already resolved successfully
        if GOLDEN_PATH.resolved and GOLDEN_PATH.root is not None:
            return GOLDEN_PATH.root

        # Already resolved unsuccessfully
        if GOLDEN_PATH.resolved and GOLDEN_PATH.root is None:
            raise_runtime_error(
                obj="GoldenRootDetectionFailed",
                msg="Cannot find Golden Root. Cannot use Data Loader.",
            )

        # First attempt
        root = get_golden_path()
        GOLDEN_PATH.root = root
        GOLDEN_PATH.resolved = True

        if root is None:
            raise_runtime_error(
                obj="GoldenRootDetectionFailed",
                msg="Cannot find Golden Root. Cannot use Data Loader.",
            )

        return root


    @classmethod
    def validate_file_path(cls, file_path, prefix=""):
        if file_path.exists():
            return
        raise ValueError(
            f"{prefix} {file_path!r} does not exist.  Cannot continue.".strip()
        )

    def validate(self):

        for prefix, file_path in (
            ("Test case folder", self.file_path),
            ("Manifest file", self.manifest_path),
            ("Input folder", self.inputs_path),
            ("Expected result folder", self.expected_results_path),
        ):
            if not file_path.exists():
                self.validate_file_path(file_path, prefix=prefix)


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
        if not os.getenv("GOLDEN_WRITE_META") and not os.getenv("GOLDEN_REGEN"):
            return

        saved = self.meta.get("saved")
        if not saved:
            return

        author = self.meta.get("author", "")
        email = self.meta.get("email", "")
        description = self.meta.get("description", "")
        notes = self.meta.get("notes", "")
        schema_version = self.meta.get("schema_version", "1.0")

        if not author:
            raise ValueError("Author name is required to generate metadata.")

        file_path = self.golden_root / self.kind / self.test_case / "meta.json"
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
        meta_out = self.file_path / "meta.json"
        write_json_atomic(meta_out, self.meta)

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


def get_directory_info(path: Path) -> DirInfo:
    directory = path if path.is_dir() else path.parent
    children = [p.name for p in directory.iterdir() if p.is_dir()]
    return DirInfo(
        parent=directory.parent.name,
        name=directory.name,
        children=children,
    )


def is_golden_root(info: DirInfo) -> bool:
    return (
        info.parent == "tests"
        and info.name == "golden"
        and "main" in info.children
        and "integration" in info.children
    )


def get_golden_path() -> Optional[Path]:
    """
    Walk upward from CWD to locate tests/golden directory.
    Fallback: check ./tests/golden relative to CWD.
    Returns the golden directory path or None.
    """
    cwd = Path.cwd()

    # Walk upward up to 10 levels
    current = cwd
    for _ in range(10):
        info = get_directory_info(current)
        if is_golden_root(info):
            return current
        current = current.parent

    # Fallback: direct relative path
    fallback = cwd / "tests" / "golden"
    if fallback.exists():
        info = get_directory_info(fallback)
        if is_golden_root(info):
            return fallback

    return None



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
