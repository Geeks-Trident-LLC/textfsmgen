import pathlib
import pytest

from ..utils import get_testcases
from textfsmgen.core.case_loader import CaseLoader
from textfsmgen.core.case_runner import CaseRunner

parent_path = pathlib.Path(__file__).parent


@pytest.mark.parametrize("test_case", get_testcases(parent_path))
def test_integration_golden(test_case):
    loader = CaseLoader(test_case)

    # Run integration golden test
    CaseRunner(loader).run()
