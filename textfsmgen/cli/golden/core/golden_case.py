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

import click

from dataclasses import dataclass
from pathlib import Path

from .data_loader import DataLoader, extract_subpath_after

from textfsmgen.libs import file


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

    @property
    def name(self):
        return extract_subpath_after("golden", self.case_dir).as_posix()

    # ------------------------------------------------------------------
    # Case type helpers
    # ------------------------------------------------------------------
    def is_main(self) -> bool:
        return self.data.is_main_case()

    def is_integration(self) -> bool:
        return self.data.is_integration_case()

    def tested(self):
        """
        Validate that this golden test case is internally consistent.

        Checks:
          • Template exists and is valid (canonical or expected depending on category)
          • Template can parse every sample in inputs/
          • All expected_results/*.json contain at least one row

        Raises:
            click.ClickException on any validation failure.
        """
        from textfsmgen.libs.common import parse_textfsm_to_dicts
        import json
        import click

        loader = self.data

        # ------------------------------------------------------------
        # 1. Load the correct template
        # ------------------------------------------------------------
        if self.is_main():
            canonical = loader.load_canonical()
            tmpl_path = canonical.template.fullname
            tmpl_content = canonical.template.content
        else:
            expected = loader.load_expected()
            tmpl_path = expected.template.fullname
            tmpl_content = expected.template.content

        if not Path(tmpl_path).exists():
            raise click.ClickException(f"Missing template: {file.path_name(tmpl_path)}")

        # Basic template validation
        try:
            _ = parse_textfsm_to_dicts(tmpl_content, "")
        except Exception as e:
            raise click.ClickException(
                f"Invalid TextFSM template ({file.path_name(tmpl_path)}): {e}"
            )

        # ------------------------------------------------------------
        # 2. Template must parse every input sample
        # ------------------------------------------------------------
        for input_info in loader.load_inputs():
            try:
                parse_textfsm_to_dicts(tmpl_content, input_info.content)
            except Exception as e:
                raise click.ClickException(
                    f"Template failed to parse input: {file.path_name(input_info.fullname)}\n{e}"
                )

        # ------------------------------------------------------------
        # 3. expected_results/*.json must contain at least one row
        # ------------------------------------------------------------
        results_dir = loader.case_dir / "expected_results"
        if not results_dir.exists():
            raise click.ClickException(
                f"Missing expected_results directory: {file.path_name(results_dir)}"
            )

        for path in sorted(results_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text())
            except Exception as e:
                raise click.ClickException(
                    f"Invalid JSON in {file.path_name(path)}: {e}"
                )

            if not isinstance(data, list):
                raise click.ClickException(
                    f"Expected list in {file.path_name(path)}, got {type(data)}"
                )

            if len(data) == 0:
                raise click.ClickException(
                    f"Expected at least one row in {file.path_name(path)}"
                )

        # ------------------------------------------------------------
        # All checks passed
        # ------------------------------------------------------------
        return True

    def check(self, other: "GoldenCase"):
        """
        Validate that two GoldenCase instances are structurally compatible.

        Checks:
          • Same builder type (from manifest)
          • Same case category (main vs integration)
          • Both cases are fully tested (self.tested())
          • Same directory structure signature:
                MAIN: (inputs, canonical, expected_results)
                INTEGRATION: (inputs, expected, expected_results)

        Raises:
            click.ClickException on mismatch.
        """

        # ------------------------------------------------------------
        # 1. Builder type must match
        # ------------------------------------------------------------
        my_builder = self.data.load_manifest().get("builder", "")
        other_builder = other.data.load_manifest().get("builder", "")

        if my_builder != other_builder:
            raise click.ClickException(
                "Builder mismatch:\n"
                f"  this case : {my_builder}\n"
                f"  other case: {other_builder}"
            )

        # ------------------------------------------------------------
        # 2. Category must match (main vs integration)
        # ------------------------------------------------------------
        if self.is_main() != other.is_main():
            raise click.ClickException(
                "Category mismatch:\n"
                f"  this case : {'main' if self.is_main() else 'integration'}\n"
                f"  other case: {'main' if other.is_main() else 'integration'}"
            )

        # ------------------------------------------------------------
        # 3. Both cases must be tested/valid
        # ------------------------------------------------------------
        try:
            self.tested()
        except Exception as e:
            raise click.ClickException(
                f"Case {file.path_name(self.case_dir)} is not tested:\n{e}"
            )

        try:
            other.tested()
        except Exception as e:
            raise click.ClickException(
                f"Case {file.path_name(other.case_dir)} is not tested:\n{e}"
            )

        # ------------------------------------------------------------
        # 4. Structure signature must match
        # ------------------------------------------------------------
        my_sig = self._structure_signature()
        other_sig = other._structure_signature()

        if my_sig != other_sig:
            raise click.ClickException(
                "Case structure mismatch:\n"
                f"  this case : {my_sig}\n"
                f"  other case: {other_sig}"
            )
        return True

    def _structure_signature(self) -> tuple[str, ...]:
        """
        Return a normalized structure signature describing which
        directories exist in this case.

        MAIN case expected:
            ('inputs', 'canonical', 'expected_results')

        INTEGRATION case expected:
            ('inputs', 'expected', 'expected_results')
        """

        base = self.case_dir

        def exists(name: str) -> bool:
            return (base / name).exists()

        sig = []

        if exists("inputs"):
            sig.append("inputs")
        if exists("canonical"):
            sig.append("canonical")
        if exists("expected"):
            sig.append("expected")
        if exists("expected_results"):
            sig.append("expected_results")

        return tuple(sig)

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
