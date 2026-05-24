# ./tests/conftest.py

from __future__ import annotations

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
