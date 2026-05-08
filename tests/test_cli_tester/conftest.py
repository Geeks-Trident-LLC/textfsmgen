import pytest

@pytest.fixture
def tmp_project(tmp_path):
    """
    Creates a minimal project structure:

    <tmp>/project/
        tests/
            golden/
                main/
                category/
                tabular/
    """
    root = tmp_path / "project"
    golden = root / "tests" / "golden"
    (golden / "main").mkdir(parents=True)
    (golden / "category").mkdir(parents=True)
    (golden / "tabular").mkdir(parents=True)
    return root
