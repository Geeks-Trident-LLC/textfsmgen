"""
Unit tests for the `textfsmgen.core.patterns.ElementPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/element_pattern/test_non_whitespace.py
    or
    $ python -m pytest tests/unit/core/element_pattern/test_non_whitespace.py
"""

import pytest

from textfsmgen.core.patterns import ElementPattern


from tests.unit.libs.pattern import (
    wss,  # noqa
    letters,  # noqa
    graph,  # noqa
    non_ws,
    non_wss,
    puncts,  # noqa
    mixed_word,  # noqa
    letter_or_punct,  # noqa
    alnums,  # noqa
    sep,
)

non_whitespace = non_ws
non_whitespaces = non_wss


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("non_ws()", f"{non_ws}"),
        ("non_wss()", f"{non_ws}+"),
        ("non_whitespace()", f"{non_whitespace}"),
        ("non_whitespaces()", f"{non_whitespace}+"),
    ],
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_non_ws()", f"{non_ws}?"),
        ("optional_non_wss()", f"{non_ws}*"),
        ("optional_non_whitespace()", f"{non_whitespace}?"),
        ("optional_non_whitespaces()", f"{non_whitespace}*"),
    ],
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_non_ws()", f"{non_ws}?"),
        ("zero_or_one_non_wss()", f"{non_ws}*"),
        ("zero_or_one_non_whitespace()", f"{non_whitespace}?"),
        ("zero_or_one_non_whitespaces()", f"{non_whitespace}*"),
    ],
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_non_ws()", f"{non_ws}*"),
        ("zero_or_more_non_wss()", f"{non_ws}*"),
        ("zero_or_more_non_whitespace()", f"{non_whitespace}*"),
        ("zero_or_more_non_whitespaces()", f"{non_whitespace}*"),
    ],
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_non_ws()", f"{non_ws}+"),
        ("one_or_more_non_wss()", f"{non_ws}+"),
        ("one_or_more_non_whitespace()", f"{non_whitespace}+"),
        ("one_or_more_non_whitespaces()", f"{non_whitespace}+"),
    ],
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("non_ws_group()", f"{non_wss}({sep}{non_wss})+"),
        ("non_wss_group()", f"{non_wss}({sep}{non_wss})+"),
        ("non_whitespace_group()", f"{non_whitespaces}({sep}{non_whitespaces})+"),
        ("non_whitespaces_group()", f"{non_whitespaces}({sep}{non_whitespaces})+"),
        ("optional_non_ws_group()", f"({non_wss}({sep}{non_wss})+)?"),
        ("optional_non_wss_group()", f"({non_wss}({sep}{non_wss})+)?"),
        (
            "optional_non_whitespace_group()",
            f"({non_whitespaces}({sep}{non_whitespaces})+)?",
        ),
        (
            "optional_non_whitespaces_group()",
            f"({non_whitespaces}({sep}{non_whitespaces})+)?",
        ),
        ("non_ws_items()", f"{non_wss}({sep}{non_wss})*"),
        ("non_wss_items()", f"{non_wss}({sep}{non_wss})*"),
        ("non_whitespace_items()", f"{non_whitespaces}({sep}{non_whitespaces})*"),
        ("non_whitespaces_items()", f"{non_whitespaces}({sep}{non_whitespaces})*"),
        ("optional_non_ws_items()", f"({non_wss}({sep}{non_wss})*)?"),
        ("optional_non_wss_items()", f"({non_wss}({sep}{non_wss})*)?"),
        (
            "optional_non_whitespace_items()",
            f"({non_whitespaces}({sep}{non_whitespaces})*)?",
        ),
        (
            "optional_non_whitespaces_items()",
            f"({non_whitespaces}({sep}{non_whitespaces})*)?",
        ),
    ],
)
def test_group(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_non_ws()", f"{non_ws}{{3}}"),
        ("three_non_wss()", f"{non_ws}{{3}}"),
        ("three_non_whitespace()", f"{non_whitespace}{{3}}"),
        ("three_non_whitespaces()", f"{non_whitespace}{{3}}"),
    ],
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_non_ws()", f"{non_ws}{{{2},{5}}}"),
        ("two_to_five_non_wss()", f"{non_ws}{{{2},{5}}}"),
        ("two_to_five_non_whitespace()", f"{non_whitespace}{{{2},{5}}}"),
        ("two_to_five_non_whitespaces()", f"{non_whitespace}{{{2},{5}}}"),
    ],
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected
