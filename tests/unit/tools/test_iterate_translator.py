"""
Unit tests for the `textfsmgen.tools.translator.IterateSuggester` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/tools/test_iterate_translator.py
    or
    $ python -m pytest tests/unit/tools/test_iterate_translator.py
"""

import pytest  # noqa

from textfsmgen.tools.translator import IterateSuggester


@pytest.mark.parametrize(
    "data, snippet, group_flag, expected",
    [
        (
            'orange is good color.',
            'word(var_name) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word(var_name) is good color."
        ),

        (
            'yellow is good color.',
            'word(var_name) word(var_v1) word(var_v2) word().',
            False,
            "word(var_name) is good word()."
        ),

        (
            'red is good color.',
            'word(var_v0, keep) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word(var_cv0) is good color."
        ),

        (
            'green is good color.',
            'word(keep, var_v0) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word(var_cv0) is good color."
        ),

        (
            'blue is good color.',
            'word(keep) word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word() is good color."
        ),

        (
            'white is good color.',
            'word() word(var_v1) word(var_v2) word(var_v3).',
            False,
            "word() word(var_v1) word(var_v2) word(var_v3)."
        ),

    ],
)
def test(data, snippet, group_flag, expected):
    node = IterateSuggester(data, snippet, group_flag=group_flag)
    assert bool(node) == True
    assert node.snippet == expected
