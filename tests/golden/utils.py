
import json
import platform
import os

import textfsmgen
import textfsm
import subprocess

from datetime import datetime

from pathlib import Path

from textfsmgen import (
    TabularTemplateBuilder,
    CategoryTemplateBuilder,
    parse_textfsm_to_dicts
)
from textfsmgen import verify_textfsm

from .case_info import GoldenCaseInfo


gold_root = Path(__file__).parent


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


class DataLoader:
    def __init__(self, kind, test_case):
        self.kind = kind
        self.test_case = test_case

        self.case_info = GoldenCaseInfo(
            kind=kind,
            name=test_case,
            path=gold_root / kind / test_case,
        )

        self.file_path = gold_root / kind / test_case
        self.manifest_path = gold_root / kind / test_case / "manifest.json"
        self.inputs_path = gold_root / kind / test_case / "inputs"
        self.expected_results_path = gold_root / kind / test_case / "expected_results"

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
        self.builder_type = result["builder_type"].lower().strip()
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

        file_path = gold_root / self.kind / self.test_case / "meta.json"
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
            * Rebuild canonical snippet
            * Rebuild canonical template
            * Rebuild canonical result.json
        - For 'integration' cases:
            * Rebuild expected snippet
            * Rebuild expected template
        - For both kinds:
            * Rebuild expected_results/*.json for each input
            * Rewrite meta.json
        """

        # Only regenerate when explicitly requested
        if not os.getenv("GOLDEN_REGEN"):
            return

        Builder = self.get_builder()

        # -----------------------------
        # 1. MAIN CASE: regenerate canonical data
        # -----------------------------
        if self.kind == "main":
            builder = Builder(
                user_data=self.canonical_sample,
                **self.parameters
            )

            # snippet
            write_text_atomic(
                self.file_path / "canonical" / "snippet.txt",
                builder.snippet
            )

            # template
            write_text_atomic(
                self.file_path / "canonical" / "textfsm.template",
                builder.template
            )

            # canonical parsed result
            rows = parse_textfsm_to_dicts(builder.template, self.canonical_sample)
            write_json_atomic(
                self.file_path / "canonical" / "result.json",
                rows
            )

        # -----------------------------
        # 2. INTEGRATION CASE: regenerate expected snippet/template
        # -----------------------------
        elif self.kind == "integration":
            # Use the FIRST input sample to regenerate expected snippet/template
            # (This is your current convention)
            first_input_info, _ = next(self.get_input_and_expected_result())
            first_input = first_input_info.get("data")

            builder = Builder(
                user_data=first_input,
                **self.parameters
            )

            write_text_atomic(
                self.file_path / "expected" / "snippet.txt",
                builder.snippet
            )

            write_text_atomic(
                self.file_path / "expected" / "textfsm.template",
                builder.template
            )

        # -----------------------------
        # 3. Regenerate expected_results for ALL inputs
        # -----------------------------
        for input_sample_info, expected_result_info in self.get_input_and_expected_result():
            input_sample = input_sample_info.get("data")
            out_path = expected_result_info.get("filename")
            rows = parse_textfsm_to_dicts(self.expected_template, input_sample)
            write_json_atomic(out_path, rows)

        # -----------------------------
        # 4. Rewrite meta.json
        # -----------------------------
        meta_out = self.file_path / "meta.json"
        write_json_atomic(meta_out, self.meta)


def get_testcases(parent_path):
    for file_path in parent_path.glob("*"):
        name = file_path.name
        if (
            file_path.is_dir() and
            (not name.startswith("_") or not name.endswith("_")) and
            name[0].isalpha()
        ):
            yield name


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


def is_identical_templates(template1, template2):
    normalized_template1 = extract_template(template1)
    normalized_template2 = extract_template(template2)
    return normalized_template1 == normalized_template2


def is_identical_snippet(snippet1, snippet2):
    return snippet1.strip() and snippet1.strip() == snippet2.strip()


def run_main_case(data_info: DataLoader) -> None:
    """
    Execute a main golden test case.

    Behavior:
    - If GOLDEN_REGEN=1: regenerate canonical + expected_results and exit early.
    - Otherwise: run normal comparisons.
    """

    # -----------------------------------
    # Regeneration mode
    # -----------------------------------
    if os.getenv("GOLDEN_REGEN"):
        data_info.regenerate()
        return  # Do NOT run comparisons during regeneration

    # -----------------------------------
    # Normal test mode
    # -----------------------------------
    Builder = data_info.get_builder()
    builder = Builder(user_data=data_info.canonical_sample, **data_info.parameters)

    error = (
        f"Failed to use canonical {data_info.kind}-format sample to create TextFSM template\n"
        "====================\n"
        f"{data_info.canonical_sample}\n"
    )
    assert bool(builder), error

    # Compare snippet
    assert is_identical_snippet(
        builder.snippet,
        data_info.canonical_snippet
    ), "Canonical snippet mismatch"

    # Compare template
    assert is_identical_templates(
        builder.template, data_info.canonical_template
    ), "Canonical template mismatch"

    # Parse canonical sample
    status = verify_textfsm(
        builder.template,
        data_info.canonical_sample,
        expected_result=data_info.canonical_result
    )
    assert bool(status), status

    # Parse each input sample
    for input_sample_info, exp_result_info in data_info.get_input_and_expected_result():
        input_sample = input_sample_info.get("data")
        exp_result = exp_result_info.get("data")
        status = verify_textfsm(
            builder.template,
            input_sample,
            expected_result=exp_result
        )
        assert bool(status), status


def run_integration_case(data_info: DataLoader) -> None:
    """
    Execute an integration golden test case.

    Behavior:
    - If GOLDEN_REGEN=1: regenerate expected + expected_results and exit early.
    - Otherwise: run normal comparisons.
    """
    # -----------------------------------
    # Regeneration mode
    # -----------------------------------
    if os.getenv("GOLDEN_REGEN"):
        data_info.regenerate()
        return  # Do NOT run comparisons during regeneration

    # -----------------------------------
    # Normal test mode
    # -----------------------------------
    Builder = data_info.get_builder()

    # Use first input sample to build expected snippet/template
    first_input_info, _ = next(data_info.get_input_and_expected_result())
    first_input = first_input_info.get("data")

    builder = Builder(
        user_data=first_input,
        **data_info.parameters
    )

    # Compare snippet
    assert is_identical_snippet(
        builder.snippet,
        data_info.expected_snippet
    ), "Expected snippet mismatch"

    # Compare template
    assert is_identical_templates(
        builder.template,
        data_info.expected_template
    ), "Expected template mismatch"

    for input_sample_info, exp_result_info in data_info.get_input_and_expected_result():
        input_sample = input_sample_info.get("data")
        exp_result = exp_result_info.get("data")
        builder = Builder(
            user_data=input_sample,
            **data_info.parameters
        )
        status = verify_textfsm(
            builder.template,
            input_sample,
            expected_result=exp_result
        )
        assert bool(status), status
