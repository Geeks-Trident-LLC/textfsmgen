"""
Unit tests for the `textfsmgen.core.testing` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/integration/environment/test.py
    or
    $ python -m pytest tests/integration/environment/test.py
"""

import pytest

from pathlib import Path, PurePath

from textfsmgen.libs import is_windows
from textfsmgen.core import testing

venv_python_path = Path(
    PurePath(
        Path.home(),
        "workspace",
        "venv_test",
        "Scripts" if is_windows else "bin",
        "python.exe" if is_windows else "python",
    )
)

file_path = Path(
    PurePath(Path.home(), "workspace", "venv_test", "Scripts", "python.exe")
)


# Skip marker if python virtual environment is not installed
skip_if_venv_unavailable = pytest.mark.skipif(
    not venv_python_path.exists(),
    reason="Skipping: python virtual environment is setup.",
)


@skip_if_venv_unavailable
def test_validate_python_executable():
    result = testing.validate_python_executable(venv_python_path)
    assert bool(result) is True, f"{result}"


@skip_if_venv_unavailable
def test_validate_textfsmgen_package():
    result = testing.validate_python_package(venv_python_path, "textfsmgen")
    assert bool(result) is True, f"{result}"


@skip_if_venv_unavailable
def test_validate_pytest_package():
    result = testing.validate_python_package(venv_python_path, "pytest")
    assert bool(result) is True, f"{result}"
