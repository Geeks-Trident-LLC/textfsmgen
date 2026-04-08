"""
Unit tests for the `textfsmgen.libs.generic` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/test_generic.py
    or
    $ python -m pytest tests/unit/libs/test_generic.py
"""

import pytest       # noqa

from textfsmgen.libs.generic import StatusString


@pytest.mark.parametrize(
    "args, exp_status, exp_text",
    [
        (["dummy fail string"],                 False,  "dummy fail string"),

        (["dummy fail string", False],          False,  "dummy fail string"),
        (["dummy fail string", "false"],        False,  "dummy fail string"),

        (["dummy true string", True],           True,   "dummy true string"),
        (["dummy true string", "true"],         True,   "dummy true string"),
        (["dummy good string", "good"],         True,   "dummy good string"),
        (["dummy pass string", "pass"],         True,   "dummy pass string"),
        (["dummy passed string", "passed"],     True,   "dummy passed string"),
        (["dummy success string", "success"],   True,   "dummy success string"),
    ],
)
def test_status_string_using_positional_arguments(args, exp_status, exp_text):
    """Verify StatusString correctly interprets positional value and status arguments."""

    result = StatusString(*args)
    assert result.status == exp_status
    assert result == exp_text


@pytest.mark.parametrize(
    "kwargs, exp_status, exp_text",
    [
        ({"text": "dummy fail string"},                         False,  "dummy fail string"),

        ({"text": "dummy fail string", "status": False},        False,  "dummy fail string"),
        ({"text": "dummy fail string", "status": "false"},      False,  "dummy fail string"),

        ({"text": "dummy true string", "status": True},         True,   "dummy true string"),
        ({"text": "dummy true string", "status": "true"},       True,   "dummy true string"),
        ({"text": "dummy good string", "status": "good"},       True,   "dummy good string"),
        ({"text": "dummy pass string", "status": "pass"},       True,   "dummy pass string"),
        ({"text": "dummy passed string", "status": "passed"},   True,   "dummy passed string"),
        ({"text": "dummy success string", "status": "success"}, True,   "dummy success string"),
    ],
)
def test_status_string_using_kwargs_arguments(kwargs, exp_status, exp_text):
    """Verify StatusString passing keyword arguments."""

    result = StatusString(**kwargs)
    assert result.status == exp_status
    assert result == exp_text


@pytest.mark.parametrize(
    "text, status, exp_status, exp_text",
    [
        ("dummy fail string",       False,      False,  "dummy fail string"),
        ("dummy fail string",       "false",    False,  "dummy fail string"),

        ("dummy true string",       True,       True,   "dummy true string"),
        ("dummy true string",       "true",     True,   "dummy true string"),
        ("dummy good string",       "good",     True,   "dummy good string"),
        ("dummy pass string",       "pass",     True,   "dummy pass string"),
        ("dummy passed string",     "passed",   True,   "dummy passed string"),
        ("dummy success string",    "success",  True,   "dummy success string"),
    ],
)
def test_status_string_mixing_positional_and_keyword_args(text, status, exp_status, exp_text):
    """Verify StatusString passing positional and keyword arguments."""

    result = StatusString(text, status=status)
    assert result.status == exp_status
    assert result == exp_text