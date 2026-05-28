# textfsmgen/core/case_loader.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Tuple

from textfsmgen.libs.generic import DotDict
from textfsmgen.exceptions import raise_runtime_error


@dataclass(frozen=True)
class GoldenCaseInfo:
    kind: str  # "main" or "integration"
    name: str
    path: Path


class CaseLoader:
    """
    Loads and validates a golden test case directory.
    Provides access to canonical/expected data and input/result pairs.
    """

    def __init__(self, test_case: str):
        self.file_path = self._validate_test_case(test_case)
        self.kind = self.file_path.parent.name
        self.name = test_case

        self.info = GoldenCaseInfo(
            kind=self.kind,
            name=test_case,
            path=self.file_path,
        )

        self.manifest_path = self.file_path / "manifest.json"
        self.inputs_path = self.file_path / "inputs"
        self.expected_results_path = self.file_path / "expected_results"

        self.canonical_dir = self.file_path / "canonical"
        self.expected_dir = self.file_path / "expected"

        # Loaded data
        self.builder_type = ""
        self.parameters = {}
        self.meta = {}

        self.canonical_sample = ""
        self.canonical_snippet = ""
        self.canonical_template = ""
        self.canonical_result = []

        self.expected_snippet = ""
        self.expected_template = ""

        self._load_manifest()
        self.load_canonical()
        self.load_expected()

    # ----------------------------------------------------------------------
    # Validation
    # ----------------------------------------------------------------------

    @classmethod
    def _validate_test_case(cls, test_case: str) -> Path | None:
        raw = Path(test_case)
        folder = raw if raw.is_absolute() else Path.cwd() / raw
        folder = folder.resolve()

        if not folder.exists() or not folder.is_dir():
            raise_runtime_error(
                obj="InvalidTestCaseStructure",
                msg=f"Test case not found or not a directory: {test_case}\nResolved: {folder}",
            )

        def require(paths):
            missing = [str(p.relative_to(folder)) for p in paths if not p.exists()]
            if missing:
                raise_runtime_error(
                    obj="InvalidTestCaseStructure",
                    msg=f"Invalid test case: {test_case}; missing: {', '.join(missing)}",
                )

        # Canonical-style
        if (folder / "canonical").exists():
            require(
                [
                    folder / "manifest.json",
                    folder / "canonical" / "sample.txt",
                    folder / "canonical" / "snippet.txt",
                    folder / "canonical" / "textfsm.template",
                    folder / "canonical" / "result.json",
                    folder / "inputs",
                    folder / "expected_results",
                ]
            )
            return folder

        # Expected-style
        if (folder / "expected").exists():
            require(
                [
                    folder / "manifest.json",
                    folder / "expected" / "snippet.txt",
                    folder / "expected" / "textfsm.template",
                    folder / "inputs",
                    folder / "expected_results",
                ]
            )
            return folder

        raise_runtime_error(
            obj="InvalidTestCaseStructure",
            msg=f"Invalid test case: {test_case}; expected canonical/ or expected/",
        )

    # ----------------------------------------------------------------------
    # Loading
    # ----------------------------------------------------------------------

    def _load_manifest(self):
        data = json.loads(self.manifest_path.read_text("utf-8"))
        self.builder_type = data["builder"].lower().strip()
        self.parameters = data["parameters"]
        self.meta = data["meta"]

    def load_canonical(self):
        if self.kind != "main":
            return

        def read(rel):
            return (self.canonical_dir / rel).read_text("utf-8")

        self.canonical_sample = read("sample.txt")
        self.canonical_snippet = read("snippet.txt")
        self.canonical_template = read("textfsm.template")
        self.canonical_result = json.loads(
            (self.canonical_dir / "result.json").read_text("utf-8")
        )

    def load_expected(self):
        if self.kind == "main":
            return

        def read(rel):
            return (self.expected_dir / rel).read_text("utf-8")

        self.expected_snippet = read("snippet.txt")
        self.expected_template = read("textfsm.template")

    # ----------------------------------------------------------------------
    # Input/result pairing
    # ----------------------------------------------------------------------

    def iter_input_result_pairs(self) -> Iterator[Tuple[DotDict, DotDict]]:
        for input_path in self.inputs_path.glob("*"):
            basename = input_path.stem
            result_path = self.expected_results_path / f"{basename}_result.json"
            if not result_path.exists():
                continue

            yield (
                DotDict(path=str(input_path), data=input_path.read_text("utf-8")),
                DotDict(
                    path=str(result_path),
                    data=json.loads(result_path.read_text("utf-8")),
                ),
            )
