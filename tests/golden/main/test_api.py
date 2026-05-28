import pathlib
import pytest
import os

from ..utils import get_testcases
from textfsmgen.core.case_loader import CaseLoader
from textfsmgen.core.case_runner import CaseRunner
from textfsmgen.core.drift_checker import DriftChecker

parent_path = pathlib.Path(__file__).parent


@pytest.mark.parametrize("test_case", get_testcases(parent_path))
def test_main_golden(test_case):
    loader = CaseLoader(test_case)

    # Run main golden test
    CaseRunner(loader).run()

    if os.getenv("CI"):
        pytest.skip("Skipping drift check in CI")

    # Check drift (main cases only)
    DriftChecker(loader).check_drift()
