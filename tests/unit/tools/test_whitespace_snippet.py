"""
Unit tests for the `textfsmgen.tools.token.WhitespaceSnippet` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/tools/test_whitespace_snippet.py
    or
    $ python -m pytest tests/unit/tools/test_whitespace_snippet.py
"""

import pytest

from textfsmgen.tools.token import WhitespaceSnippet


@pytest.mark.parametrize(
    "items, options, parsed, snippet",
    [
        # basic whitespace
        ((" ",), {"var_name": "", "generic": False}, True, "spaces()"),
        ((" \t ",), {"var_name": "", "generic": False}, True, "wss()"),
        # with variable name
        ((" ",), {"var_name": "v0", "generic": False}, True, "spaces(var_v0)"),
        ((" \t ",), {"var_name": "v1", "generic": False}, True, "wss(var_v1)"),
        # allow empty
        (
            (" ", "", "   "),
            {"var_name": "v0", "generic": False},
            True,
            "spaces(var_v0, or_empty)",
        ),
        (
            (" \t ", "", "  "),
            {"var_name": "v1", "generic": False},
            True,
            "wss(var_v1, or_empty)",
        ),
        # generic=True behaves the same
        (
            (" ", "", "   "),
            {"var_name": "v0", "generic": True},
            True,
            "spaces(var_v0, or_empty)",
        ),
        (
            (" \t ", "", "  "),
            {"var_name": "v1", "generic": True},
            True,
            "wss(var_v1, or_empty)",
        ),
        # invalid: contains non-whitespace
        ((" ", "", " a  "), {"var_name": "v0", "generic": False}, False, ""),
        ((" \t ", "", " b "), {"var_name": "v1", "generic": False}, False, ""),
    ],
)
def test_whitespace_snippet(items, options, parsed, snippet):
    node = WhitespaceSnippet(*items, **options)
    assert bool(node) == parsed
    assert node.snippet == snippet
