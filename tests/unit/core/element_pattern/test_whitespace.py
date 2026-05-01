"""
Unit tests for the `textfsmgen.core.patterns.ElementPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/element_pattern/test_whitespace.py
    or
    $ python -m pytest tests/unit/core/element_pattern/test_whitespace.py
"""

import pytest   # noqa

from textfsmgen.core.patterns import ElementPattern


from tests.unit.libs.pattern import (
    space, spaces, ws, wss,                     # noqa
    dot, letter, letters,                       # noqa
    digit, digits, alnum, graph,                # noqa
    non_ws, non_wss, punct, puncts,             # noqa
    number, mixed_number, word, mixed_word,     # noqa
    space_or_punct, letter_or_punct,            # noqa
    alnum, alnums,                              # noqa

    sep
)

whitespace = ws
whitespaces = wss


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("ws()",            f"{ws}"),
        ("wss()",           f"{ws}+"),
        ("whitespace()",    f"{whitespace}"),
        ("whitespaces()",   f"{whitespace}+"),
    ]
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_ws()",           f"{ws}?"),
        ("optional_wss()",          f"{ws}*"),
        ("optional_whitespace()",   f"{whitespace}?"),
        ("optional_whitespaces()",  f"{whitespace}*"),
    ]
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_ws()",            f"{ws}?"),
        ("zero_or_one_wss()",           f"{ws}*"),
        ("zero_or_one_whitespace()",    f"{whitespace}?"),
        ("zero_or_one_whitespaces()",   f"{whitespace}*"),
    ]
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_ws()",           f"{ws}*"),
        ("zero_or_more_wss()",          f"{ws}*"),
        ("zero_or_more_whitespace()",   f"{whitespace}*"),
        ("zero_or_more_whitespaces()",  f"{whitespace}*"),
    ]
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_ws()",            f"{ws}+"),
        ("one_or_more_wss()",           f"{ws}+"),
        ("one_or_more_whitespace()",    f"{whitespace}+"),
        ("one_or_more_whitespaces()",   f"{whitespace}+"),
    ]
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("ws_group()",                      f"{ws}+"),
        ("wss_group()",                     f"{ws}+"),
        ("whitespace_group()",              f"{ws}+"),
        ("whitespaces_group()",             f"{ws}+"),

        ("optional_ws_group()",             f"{ws}*"),
        ("optional_wss_group()",            f"{ws}*"),
        ("optional_whitespace_group()",     f"{ws}*"),
        ("optional_whitespaces_group()",    f"{ws}*"),

        ("ws_items()",                      f"{ws}+"),
        ("wss_items()",                     f"{ws}+"),
        ("whitespace_items()",              f"{ws}+"),
        ("whitespaces_items()",             f"{ws}+"),

        ("optional_ws_items()",             f"{ws}*"),
        ("optional_wss_items()",            f"{ws}*"),
        ("optional_whitespace_items()",     f"{ws}*"),
        ("optional_whitespaces_items()",    f"{ws}*"),
    ]
)
def test_group(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_ws()",              f"{ws}{{3}}"),
        ("three_wss()",             f"{ws}{{3}}"),
        ("three_whitespace()",      f"{whitespace}{{3}}"),
        ("three_whitespaces()",     f"{whitespace}{{3}}"),
    ]
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected

@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_ws()",            f"{ws}{{{2},{5}}}"),
        ("two_to_five_wss()",           f"{ws}{{{2},{5}}}"),
        ("two_to_five_whitespace()",    f"{whitespace}{{{2},{5}}}"),
        ("two_to_five_whitespaces()",   f"{whitespace}{{{2},{5}}}"),
    ]
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected