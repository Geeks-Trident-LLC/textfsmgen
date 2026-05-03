"""
Unit tests for the `textfsmgen.exceptions.raise_runtime_exception` function.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/test_exceptions.py
    or
    $ python -m pytest tests/unit/test_exceptions.py
"""

import pytest   # noqa

from textfsmgen.exceptions import raise_runtime_error

from tests.unit import DummyClass


def test_raise_with_runtime_error():
    """
    Verify that `raise_runtime_error` defaults to `RuntimeError` when `obj` is None.
    """
    with pytest.raises(Exception) as exc_info:
        raise_runtime_error(None, "generic failure")
    exc = exc_info.value
    assert exc.__class__.__name__ == "RuntimeError"
    assert str(exc) == "generic failure"

def test_raise_with_string():
    """
    Verify that `raise_runtime_error` raises a custom exception when
    given a string name.
    """
    with pytest.raises(Exception) as exc_info:
        raise_runtime_error("AnotherError", "bad input")
    exc = exc_info.value
    assert exc.__class__.__name__ == "AnotherError"
    assert str(exc) == "bad input"

def test_raise_with_object():
    """
    Verify that `raise_runtime_error` derives the exception class name
    from an object.
    """
    obj = DummyClass()
    with pytest.raises(Exception) as exc_info:
        raise_runtime_error(obj, "dummy failure")
    exc = exc_info.value
    assert exc.__class__.__name__ == "DummyClassRTError"
    assert str(exc) == "dummy failure"