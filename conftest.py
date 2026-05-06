def pytest_addoption(parser):
    parser.addoption("--enable-golden", action="store_true",
                     help="Enable golden test framework")
    parser.addoption("--debug-golden", action="store_true",
                     help="Debug golden test cases")
    parser.addoption("--diff-golden", action="store_true",
                     help="Show unified diff when golden mismatch")


def pytest_configure(config):
    # Expose a simple boolean flag for golden mode
    config.is_golden_enabled = config.getoption("--enable-golden")
