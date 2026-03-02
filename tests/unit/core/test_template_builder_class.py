"""
Unit tests for the `textfsmgen.core.TemplateBuilder` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/test_template_builder_class.py
    or
    $ python -m pytest tests/unit/core/test_template_builder_class.py
"""

from textfsmgen.core.template import TemplateBuilder

from tests.unit.core import get_user_data
from tests.unit.core import get_expected_template
from tests.unit.core import get_test_data
from tests.unit.core import get_expected_result


def test_generate_textfsm_template():
    user_data = get_user_data(case="case1")
    expected_template = get_expected_template(case="case1")

    factory = TemplateBuilder(user_data=user_data)
    assert factory.template == expected_template


def test_generate_textfsm_template_with_comment_and_kept_flag():
    user_data = get_user_data(case="case2")
    expected_template = get_expected_template(case="case2")

    factory = TemplateBuilder(user_data=user_data)
    assert factory.template == expected_template

def test_template_builder_verify_method():
    user_data = get_user_data()
    test_data = get_test_data()

    factory = TemplateBuilder(user_data=user_data, test_data=test_data)
    is_verified = factory.verify()
    assert is_verified is True


def test_template_builder_verify_method_expected_rows_count():
    user_data = get_user_data()
    test_data = get_test_data()
    expected_rows_count = len(get_expected_result())

    factory = TemplateBuilder(user_data=user_data, test_data=test_data,)
    is_verified = factory.verify(expected_rows_count=expected_rows_count)
    assert is_verified is True


def test_template_builder_verify_method_expected_result():
    user_data = get_user_data()
    test_data = get_test_data()
    expected_result = get_expected_result()
    expected_rows_count = len(expected_result)

    factory = TemplateBuilder(user_data=user_data, test_data=test_data)
    is_verified = factory.verify(
        expected_rows_count=expected_rows_count,
        expected_result=expected_result
    )
    assert is_verified is True