import pathlib
import pytest

from tests.golden import get_testcases, DataLoader, run_main_case

parent_path = pathlib.Path(__file__).parent


@pytest.mark.parametrize("test_case", get_testcases(parent_path))
def test_main_golden(test_case):
    kind = parent_path.name  # "main"
    data_info = DataLoader(kind, test_case)
    run_main_case(data_info)
