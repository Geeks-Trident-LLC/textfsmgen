"""
Unit tests for the `textfsmgen.tools.translator.IterateTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/tools/test_iterate_translator.py
    or
    $ python -m pytest tests/unit/tools/test_iterate_translator.py
"""

import pytest  # noqa

from textfsmgen.tools.translator import IterateTranslator


@pytest.mark.parametrize(
    "data, snippet, group_flag, expected",
    [
        (
            'red is good color.',
            'word(var_v0, keep) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word(var_v0) is good color."
        ),

        (
            'red is good color.',
            'word(keep, var_v0) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word(var_v0) is good color."
        ),

        (
            'red is good color.',
            'word(keep) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word() is good color."
        ),

    ],
)
def test(data, snippet, group_flag, expected):
    node = IterateTranslator(data, snippet, group_flag=group_flag)
    assert bool(node) == True
    assert node.snippet == expected
