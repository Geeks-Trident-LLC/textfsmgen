import pathlib
import pytest

from tests.golden import get_testcases, run_integration_case
from textfsmgen.core.data_loader import DataLoader

parent_path = pathlib.Path(__file__).parent


@pytest.mark.parametrize("test_case", get_testcases(parent_path))
def test_integration_golden(test_case):
    data_info = DataLoader(test_case)
    run_integration_case(data_info)
