import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--regen-golden",
        action="store_true",
        help="Regenerate golden data instead of verifying"
    )

@pytest.fixture
def regen_golden(request):
    return request.config.getoption("--regen-golden")
