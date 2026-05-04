"""
Unit tests for the `textfsmgen.core.patterns.ElementPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/element_pattern/test_punctuation.py
    or
    $ python -m pytest tests/unit/core/element_pattern/test_punctuation.py
"""

import pytest

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

non_whitespace = non_ws
non_whitespaces = non_wss
punctuation = punct
punctuations = puncts


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("punct()",         f"{punct}"),
        ("puncts()",        f"{punct}+"),
        ("punctuation()",   f"{punctuation}"),
        ("punctuations()",  f"{punctuation}+"),
    ]
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_punct()",        f"{punct}?"),
        ("optional_puncts()",       f"{punct}*"),
        ("optional_punctuation()",  f"{punctuation}?"),
        ("optional_punctuations()", f"{punctuation}*"),
    ]
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_punct()",         f"{punct}?"),
        ("zero_or_one_puncts()",        f"{punct}*"),
        ("zero_or_one_punctuation()",   f"{punctuation}?"),
        ("zero_or_one_punctuations()",  f"{punctuation}*"),
    ]
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_punct()",        f"{punct}*"),
        ("zero_or_more_puncts()",       f"{punct}*"),
        ("zero_or_more_punctuation()",  f"{punctuation}*"),
        ("zero_or_more_punctuations()", f"{punctuation}*"),
    ]
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_punct()",         f"{punct}+"),
        ("one_or_more_puncts()",        f"{punct}+"),
        ("one_or_more_punctuation()",   f"{punctuation}+"),
        ("one_or_more_punctuations()",  f"{punctuation}+"),
    ]
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("punct_group()",                   f"{puncts}({sep}{puncts})+"),
        ("puncts_group()",                  f"{puncts}({sep}{puncts})+"),
        ("punctuation_group()",             f"{punctuations}({sep}{punctuations})+"),
        ("punctuations_group()",            f"{punctuations}({sep}{punctuations})+"),

        ("optional_punct_group()",          f"({puncts}({sep}{puncts})+)?"),
        ("optional_puncts_group()",         f"({puncts}({sep}{puncts})+)?"),
        ("optional_punctuation_group()",    f"({punctuations}({sep}{punctuations})+)?"),
        ("optional_punctuations_group()",   f"({punctuations}({sep}{punctuations})+)?"),

        ("punct_items()",                   f"{puncts}({sep}{puncts})*"),
        ("puncts_items()",                  f"{puncts}({sep}{puncts})*"),
        ("punctuation_items()",             f"{punctuations}({sep}{punctuations})*"),
        ("punctuations_items()",            f"{punctuations}({sep}{punctuations})*"),

        ("optional_punct_items()",          f"({puncts}({sep}{puncts})*)?"),
        ("optional_puncts_items()",         f"({puncts}({sep}{puncts})*)?"),
        ("optional_punctuation_items()",    f"({punctuations}({sep}{punctuations})*)?"),
        ("optional_punctuations_items()",   f"({punctuations}({sep}{punctuations})*)?"),
    ]
)
def test_group(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_punct()",           f"{punct}{{3}}"),
        ("three_puncts()",          f"{punct}{{3}}"),
        ("three_punctuation()",     f"{punctuation}{{3}}"),
        ("three_punctuations()",    f"{punctuation}{{3}}"),
    ]
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected

@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_punct()",         f"{punct}{{{2},{5}}}"),
        ("two_to_five_puncts()",        f"{punct}{{{2},{5}}}"),
        ("two_to_five_punctuation()",   f"{punctuation}{{{2},{5}}}"),
        ("two_to_five_punctuations()",  f"{punctuation}{{{2},{5}}}"),
    ]
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected