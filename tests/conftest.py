# ./tests/conftest.py

from __future__ import annotations

import json
import pytest
import os
from pathlib import Path
from dataclasses import dataclass
from textfsmgen import FreeFormBuilder, CategoryBuilder, TabularBuilder

from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def valid_case(tmp_path):
    """
    Creates a fully valid minimal INTEGRATION golden test case:

    integration/demo/
        inputs/demo.txt
        expected_results/demo_result.json
        expected/textfsm.template
        expected/snippet.txt
        manifest.json
    """

    case = tmp_path / "tests" / "golden" / "integration" / "demo"
    case.mkdir(parents=True)

    # Directories
    (case / "inputs").mkdir()
    (case / "expected_results").mkdir()
    (case / "expected").mkdir()

    # Minimal valid TextFSM template
    template = """\
Value name (\\S+)

Start
  ^${name}$$ -> Record
"""
    (case / "expected" / "textfsm.template").write_text(template)

    # Minimal snippet (not used by parser but required)
    (case / "expected" / "snippet.txt").write_text("word(var_name)")

    # Input file
    (case / "inputs" / "demo.txt").write_text("hello")

    # Expected result
    expected = [{"name": "hello"}]
    (case / "expected_results" / "demo_result.json").write_text(
        json.dumps(expected, indent=2)
    )

    # Manifest
    manifest = {
        "name": "demo",
        "author": "tester",
        "description": "valid minimal test case",
        "version": 1,
    }
    (case / "manifest.json").write_text(json.dumps(manifest, indent=2))

    return case


@pytest.fixture
def tmpcase(tmp_path):
    """Creates a minimal golden test case directory."""
    case = tmp_path / "tests" / "golden" / "integration" / "demo"
    case.mkdir(parents=True)

    # minimal authoritative files
    (case / "inputs").mkdir()
    (case / "expected_results").mkdir()
    (case / "expected").mkdir()

    (case / "inputs" / "demo.txt").write_text("hello")
    (case / "expected_results" / "demo_result.json").write_text("[]")
    (case / "expected" / "textfsm.template").write_text("")
    (case / "expected" / "snippet.txt").write_text("")

    return case


@pytest.fixture
def tmpfile(tmp_path):
    def _make(name, content=""):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    return _make


@pytest.fixture
def fake_builder_factory():
    """
    Factory that returns a FakeBuilder subclass matching the requested base class.
    Ensures issubclass(FakeBuilder, BaseBuilder) is True.
    """

    def _factory(base_cls):
        @dataclass
        class FakeBuildResult:
            snippet: str
            template: str
            result: list
            warning: str | None = None

        class FakeBuilder(base_cls):
            def __init__(self):
                self.sample = None
                self.params = None
                self.snippet = "abc"
                self.template = "Value {{ key }}"
                self.result = []
                self.warning = None

            def set_sample(self, sample, **params):
                self.sample = sample
                self.params = params

            def set_snippet(self, snippet):
                self.snippet = snippet

            def set_snippet_file(self, path):
                self.snippet = f"FILE:{path}"

            def build(self):
                if self.sample and "fail" in self.sample:
                    self.result = []
                    self.warning = "Template could not parse sample"
                elif self.sample:
                    self.result = [{"key": "value"}]
                else:
                    self.result = []

            def to_result(self):
                return FakeBuildResult(
                    snippet=self.snippet,
                    template=self.template,
                    result=self.result,
                    warning=self.warning,
                )

        return FakeBuilder

    return _factory


# ------------------------------------------------------------
# Builder-specific fixtures (correct)
# ------------------------------------------------------------


@pytest.fixture
def fake_freeform(fake_builder_factory):
    return fake_builder_factory(FreeFormBuilder)


@pytest.fixture
def fake_category(fake_builder_factory):
    return fake_builder_factory(CategoryBuilder)


@pytest.fixture
def fake_tabular(fake_builder_factory):
    return fake_builder_factory(TabularBuilder)


@pytest.fixture
def fake_builder(fake_builder_factory):
    return fake_builder_factory(FreeFormBuilder)


@pytest.fixture
def patch_builder(monkeypatch):
    """
    Patch BUILDER_MAPPING so CLI uses fake builders.
    This fixture does NOT know which builder is needed.
    Tests must call it like:

        patch_builder("tabular", fake_tabular)
    """

    def _patch(name, fake_cls):
        import textfsmgen.cli.shared_builder_cli as sbc

        monkeypatch.setitem(sbc.BUILDER_MAPPING, name, fake_cls)

    return _patch


# ------------------------------------------------------------
# Patch load_sample globally for all CLI tests
# ------------------------------------------------------------


@pytest.fixture
def patch_load_sample(monkeypatch):
    monkeypatch.setattr(
        "textfsmgen.cli.shared_builder_cli.load_sample",
        lambda sf, cmd: "SAMPLE TEXT",
    )


def pytest_addoption(parser):
    parser.addoption(
        "--regen-golden",
        action="store_true",
        default=False,
        help="Regenerate golden files instead of comparing them.",
    )


def pytest_configure(config):
    if config.getoption("--regen-golden"):
        os.environ["GOLDEN_REGEN"] = "1"
        print("\n[golden] Regenerating golden files...\n")


@pytest.fixture
def regen_golden(request):
    return request.config.getoption("--regen-golden")


def pytest_collection_modifyitems(config, items):
    """
    Skip all tests under tests/golden unless --regen-golden is passed.
    """
    regen = config.getoption("--regen-golden")

    if regen:
        # Running: pytest tests/golden --regen-golden
        return

    # Running: pytest tests/golden
    skip_marker = pytest.mark.skip(reason="Golden tests require --regen-golden")

    for item in items:
        # Only skip tests inside tests/golden/
        if Path("tests/golden") in Path(item.fspath).parents:
            item.add_marker(skip_marker)
