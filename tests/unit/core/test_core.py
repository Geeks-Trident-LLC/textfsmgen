"""
Unit tests for `textfsmgen.core` functions: `get_textfsm_template` and `verify`.

This module validates the behavior of two core functions used in the
TextFSM Generator workflow:

Usage
-----
Run pytest in the project root to execute these tests:

    $ pytest tests/unit/core/test_core.py
    or
    $ python -m pytest tests/unit/core/test_core.py
"""

from textfsmgen.verify import verify
from textfsmgen.core import get_textfsm_template

from tests.unit.core import get_user_data
from tests.unit.core import get_expected_template
from tests.unit.core import get_test_data
from tests.unit.core import get_expected_result


def test_get_textfsm_template_func():
    """
    Ensures that a TextFSM template is correctly generated from user data
    snippets and matches the expected template output.
    """
    user_data = get_user_data()
    expected_template = get_expected_template()

    textfsm_template = get_textfsm_template(template_snippet=user_data)
    assert textfsm_template == expected_template


def test_verify_func():
    """
    Confirms that a generated template can parse test data correctly.
    The parsed output is validated against expected results and row counts.
    """
    user_data = get_user_data()
    test_data = get_test_data()
    expected_result = get_expected_result()
    expected_rows_count = len(expected_result)

    is_verified = verify(
        template_snippet=user_data,
        test_data=test_data,
        expected_rows_count=expected_rows_count,
        expected_result=expected_result
    )
    assert is_verified is True