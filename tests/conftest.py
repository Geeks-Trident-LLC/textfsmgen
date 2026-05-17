import pytest
import os
from pathlib import Path

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
def fake_builder():
    class FakeBuilder:
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

        def build(self):
            # keep it simple but realistic
            if self.sample and "fail" in self.sample:
                self.result = []
                self.warning = "Template could not parse sample"
            elif self.sample:
                self.result = [{"key": "value"}]
            else:
                self.result = []

        def __bool__(self):
            return True

    return FakeBuilder


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
