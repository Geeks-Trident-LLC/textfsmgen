"""
Unit tests for the `textfsmgen.libs.generic.StatusString` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/test_status_string.py
    or
    $ python -m pytest tests/unit/libs/test_status_string.py
"""

import pytest

from textfsmgen.libs.generic import StatusString


@pytest.mark.parametrize(
    "args, exp_status, exp_text",
    [
        (["dummy fail"], False, "dummy fail"),
        (["dummy fail", False], False, "dummy fail"),
        (["dummy fail", "false"], False, "dummy fail"),
        (["dummy true", True], True, "dummy true"),
        (["dummy true", "true"], True, "dummy true"),
        (["dummy good", "good"], True, "dummy good"),
        (["dummy pass", "pass"], True, "dummy pass"),
        (["dummy passed", "passed"], True, "dummy passed"),
        (["dummy success", "success"], True, "dummy success"),
    ],
)
def test_using_positional_arguments(args, exp_status, exp_text):
    """Verify StatusString correctly interprets positional value and status arguments."""

    result = StatusString(*args)
    assert result.status == exp_status
    assert result == exp_text


@pytest.mark.parametrize(
    "kwargs, exp_status, exp_text",
    [
        ({"text": "dummy fail"}, False, "dummy fail"),
        ({"value": "dummy fail", "status": False}, False, "dummy fail"),
        ({"data": "dummy fail", "status": "false"}, False, "dummy fail"),
        ({"text": "dummy true", "status": True}, True, "dummy true"),
        ({"value": "dummy true", "status": "true"}, True, "dummy true"),
        ({"data": "dummy good", "status": "good"}, True, "dummy good"),
        ({"text": "dummy pass", "status": "pass"}, True, "dummy pass"),
        ({"value": "dummy passed", "status": "passed"}, True, "dummy passed"),
        ({"data": "dummy success", "status": "success"}, True, "dummy success"),
    ],
)
def test_using_kwargs_arguments(kwargs, exp_status, exp_text):
    """Verify StatusString passing keyword arguments."""

    result = StatusString(**kwargs)
    assert result.status == exp_status
    assert result == exp_text


@pytest.mark.parametrize(
    "text, status, reason, expected",
    [
        ("dummy fail", False, "dummy reason", False),
        ("dummy fail", "false", "dummy reason", False),
        ("dummy true", True, "dummy reason", True),
        ("dummy true", "true", "dummy reason", True),
        ("dummy good", "good", "dummy good", True),
        ("dummy pass", "pass", "dummy pass", True),
        ("dummy passed", "passed", "dummy passed", True),
        ("dummy success", "success", "dummy success", True),
    ],
)
def test_mixing_positional_and_keyword_args(text, status, reason, expected):
    """Verify StatusString passing positional and keyword arguments."""

    result = StatusString(text, status=status, reason=reason)
    assert result == text
    assert bool(result) is expected
    assert result.reason == reason

    result = StatusString(text, status=status, message=reason)
    assert bool(result) is expected
    assert result == text
    assert result.reason == reason
