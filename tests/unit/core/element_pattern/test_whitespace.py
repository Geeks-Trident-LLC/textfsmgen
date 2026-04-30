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


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("space()",         r" "),
        ("spaces()",        r" +"),
        ("ws()",            r"\s"),
        ("wss()",           r"\s+"),
        ("whitespace()",    r"\s"),
        ("whitespaces()",   r"\s+"),
    ]
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_space()",         r" ?"),
        ("optional_spaces()",        r" *"),
        ("optional_ws()",            r"\s?"),
        ("optional_wss()",           r"\s*"),
        ("optional_whitespace()",    r"\s?"),
        ("optional_whitespaces()",   r"\s*"),
    ]
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_space()",         r" ?"),
        ("zero_or_one_spaces()",        r" *"),
        ("zero_or_one_ws()",            r"\s?"),
        ("zero_or_one_wss()",           r"\s*"),
        ("zero_or_one_whitespace()",    r"\s?"),
        ("zero_or_one_whitespaces()",   r"\s*"),
    ]
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_space()",         r" *"),
        ("zero_or_more_spaces()",        r" *"),
        ("zero_or_more_ws()",            r"\s*"),
        ("zero_or_more_wss()",           r"\s*"),
        ("zero_or_more_whitespace()",    r"\s*"),
        ("zero_or_more_whitespaces()",   r"\s*"),
    ]
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_space()",         r" +"),
        ("one_or_more_spaces()",        r" +"),
        ("one_or_more_ws()",            r"\s+"),
        ("one_or_more_wss()",           r"\s+"),
        ("one_or_more_whitespace()",    r"\s+"),
        ("one_or_more_whitespaces()",   r"\s+"),
    ]
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_space()",         r" {3}"),
        ("three_spaces()",        r" {3}"),
        ("three_ws()",            r"\s{3}"),
        ("three_wss()",           r"\s{3}"),
        ("three_whitespace()",    r"\s{3}"),
        ("three_whitespaces()",   r"\s{3}"),
    ]
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected

@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_space()",         r" {2,5}"),
        ("two_to_five_spaces()",        r" {2,5}"),
        ("two_to_five_ws()",            r"\s{2,5}"),
        ("two_to_five_wss()",           r"\s{2,5}"),
        ("two_to_five_whitespace()",    r"\s{2,5}"),
        ("two_to_five_whitespaces()",   r"\s{2,5}"),
    ]
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected