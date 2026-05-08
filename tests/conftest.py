import pytest
import os

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
