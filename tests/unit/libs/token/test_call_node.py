"""
Unit tests for the `textfsmgen.libs.token.CallNode` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/token/test_call_node.py
    or
    $ python -m pytest tests/unit/libs/token/test_call_node.py
"""

import pytest   # noqa

from textfsmgen.libs.token import CallNode

@pytest.mark.parametrize(
    "data, exp_name, exp_params",
    [
        ("word()", "word", []),
        ("word(var_name, or_empty)", "word", ["var_name", "or_empty"]),
        ("word(var_name, digits())", "word", ["var_name", "digits()"]),
    ]
)
def test(data, exp_name, exp_params):
    call_node = CallNode(data)
    assert bool(call_node)
    assert call_node.name == exp_name
    assert call_node.params == exp_params