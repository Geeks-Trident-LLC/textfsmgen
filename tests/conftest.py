import pytest
import os
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--regen-golden",
        action="store_true",
        default=False,
        help="Regenerate golden files instead of comparing them."
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
