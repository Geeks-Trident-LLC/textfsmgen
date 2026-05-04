"""
Unit tests for the `textfsmgen.libs.token.TextNode` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/token/test_call_node.py
    or
    $ python -m pytest tests/unit/libs/token/test_call_node.py
"""

import pytest

from textfsmgen.libs.token import TextNode


@pytest.mark.parametrize(
    "data,expected",
    [
        (b"Hello Python", "Hello Python"),
        ("Hello Python", "Hello Python"),
        (None, ""),
        (1, "1"),
        (True, "True"),
        ({"first": "green", "second": "blue"}, "{'first': 'green', 'second': 'blue'}"),
    ],
)
def test(data, expected):
    text_node = TextNode(data)
    assert text_node == expected
