from tests.integration.golden.utils import iter_testcases

def test_list_golden_runs(pytester):
    result = pytester.runpytest("--list-golden")
    result.stdout.fnmatch_lines(["Golden Test Cases:*"])
    result.assert_outcomes()

def test_new_golden_scaffold(pytester, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests/integration/golden").mkdir(parents=True)
    (tmp_path / "tests/conftest.py").write_text(
        'pytest_plugins = ["tests.integration.golden.integration_plugin"]'
    )

    result = pytester.runpytest("--new-golden", "demo/newcase")
    result.stdout.fnmatch_lines(["Created new golden test case scaffold*"])
    assert (tmp_path / "tests/integration/golden/demo/newcase").exists()

def test_parametrization(pytester):
    cases = list(iter_testcases())
    assert isinstance(cases, list)
    assert all(len(c) == 3 for c in cases)
