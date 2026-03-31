"""
Unit tests for the `textfsmgen.gpcategory.CategoryLineTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/category/test_lines_to_regex.py
    or
    $ python -m pytest tests/unit/engine/category/test_lines_to_regex.py
"""
import re
import pytest

from textfsmgen.core.template import get_textfsm_template
from textfsmgen.core.verify import verify

from textfsmgen.engine.category import CategoryLinesTranslator

from tests.unit import replace_dates_with_placeholder

from textfsmgen.libs.decorators import normalize_output


@normalize_output
def get_test_data():
    return """
        fruits: orange, peach
        meat: pork
        drinks: water
        """


@normalize_output
def get_expected_pattern():
    fruits_pat = r"fruits: *(?P<fruits>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+)(\r?\n|\r)"  # noqa
    meat_pat = r"meat: *(?P<meat>[a-zA-Z]+)(\r?\n|\r)"
    drink_pat = r"drinks: *(?P<drinks>[a-zA-Z]+)"
    exp_pattern = f"{fruits_pat}{meat_pat}{drink_pat}"
    return exp_pattern


def get_expected_result():
    return {
        'fruits': 'orange, peach',
        'meat': 'pork',
        'drinks': 'water'
    }


def test():
    test_data = get_test_data()
    exp_pattern = get_expected_pattern()
    exp_result = get_expected_result()

    # --- Action ---
    node = CategoryLinesTranslator(test_data)
    pattern = node.to_regex()

    # --- Assertions ---
    assert pattern == exp_pattern, (
        f"Generated pattern {pattern!r} does not match expected {exp_pattern!r}"
    )

    match = re.match(pattern, test_data)
    if match:
        result = match.groupdict()
        assert result == exp_result, (
            f"Regex groups {result} do not match expected {exp_result}"
        )
    else:
        pytest.fail(f"No match found. Expected pattern: {pattern!r}")
