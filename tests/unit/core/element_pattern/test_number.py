"""
Unit tests for the `textfsmgen.core.patterns.ElementPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/element_pattern/test_number.py
    or
    $ python -m pytest tests/unit/core/element_pattern/test_number.py
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

@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("digit()",         f"{digit}"),
        ("digits()",        f"{digit}+"),
        ("number()",        f"{number}"),
        ("numbers()",       f"{number}({sep}{number})*"),
        ("mixed_number()",  f"{mixed_number}"),
        ("mixed_numbers()", f"{mixed_number}({sep}{mixed_number})*"),
    ]
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_digit()",            f"{digit}?"),
        ("optional_digits()",           f"{digit}*"),
        ("optional_number()",           f"({number})?"),
        ("optional_numbers()",          f"({number}({sep}{number})*)?"),
        ("optional_mixed_number()",     f"({mixed_number})?"),
        ("optional_mixed_numbers()",    f"({mixed_number}({sep}{mixed_number})*)?"),
    ]
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_digit()",         f"{digit}?"),
        ("zero_or_one_digits()",        f"{digit}*"),
        ("zero_or_one_number()",        f"({number})?"),
        ("zero_or_one_numbers()",       f"({number}({sep}{number})*)?"),
        ("zero_or_one_mixed_number()",  f"({mixed_number})?"),
        ("zero_or_one_mixed_numbers()", f"({mixed_number}({sep}{mixed_number})*)?"),
    ]
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_digit()",            f"{digit}*"),
        ("zero_or_more_digits()",           f"{digit}*"),
        ("zero_or_more_number()",           f"({number}({sep}{number})*)?"),
        ("zero_or_more_numbers()",          f"({number}({sep}{number})*)?"),
        ("zero_or_more_mixed_number()",     f"({mixed_number}({sep}{mixed_number})*)?"),
        ("zero_or_more_mixed_numbers()",    f"({mixed_number}({sep}{mixed_number})*)?"),
    ]
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_digit()",         f"{digit}+"),
        ("one_or_more_digits()",        f"{digit}+"),
        ("one_or_more_number()",        f"{number}({sep}{number})*"),
        ("one_or_more_numbers()",       f"{number}({sep}{number})*"),
        ("one_or_more_mixed_number()",  f"{mixed_number}({sep}{mixed_number})*"),
        ("one_or_more_mixed_numbers()", f"{mixed_number}({sep}{mixed_number})*"),
    ]
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("digit_group()",           f"{digits}({sep}{digits})+"),
        ("digits_group()",          f"{digits}({sep}{digits})+"),
        ("number_group()",          f"{number}({sep}{number})+"),
        ("numbers_group()",         f"{number}({sep}{number})+"),
        ("mixed_number_group()",    f"{mixed_number}({sep}{mixed_number})+"),
        ("mixed_numbers_group()",   f"{mixed_number}({sep}{mixed_number})+"),

        ("optional_digit_group()",          f"({digits}({sep}{digits})+)?"),
        ("optional_digits_group()",         f"({digits}({sep}{digits})+)?"),
        ("optional_number_group()",         f"({number}({sep}{number})+)?"),
        ("optional_numbers_group()",        f"({number}({sep}{number})+)?"),
        ("optional_mixed_number_group()",   f"({mixed_number}({sep}{mixed_number})+)?"),
        ("optional_mixed_numbers_group()",  f"({mixed_number}({sep}{mixed_number})+)?"),

        ("digit_items()",           f"{digits}({sep}{digits})*"),
        ("digits_items()",          f"{digits}({sep}{digits})*"),
        ("number_items()",          f"{number}({sep}{number})*"),
        ("numbers_items()",         f"{number}({sep}{number})*"),
        ("mixed_number_items()",    f"{mixed_number}({sep}{mixed_number})*"),
        ("mixed_numbers_items()",   f"{mixed_number}({sep}{mixed_number})*"),

        ("optional_digit_items()",          f"({digits}({sep}{digits})*)?"),
        ("optional_digits_items()",         f"({digits}({sep}{digits})*)?"),
        ("optional_number_items()",         f"({number}({sep}{number})*)?"),
        ("optional_numbers_items()",        f"({number}({sep}{number})*)?"),
        ("optional_mixed_number_items()",   f"({mixed_number}({sep}{mixed_number})*)?"),
        ("optional_mixed_numbers_items()",  f"({mixed_number}({sep}{mixed_number})*)?"),

    ]
)
def test_group(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_digit()",           f"{digit}{{3}}"),
        ("three_digits()",          f"{digit}{{3}}"),
        ("three_number()",          f"{number}({sep}{number}){{2}}"),
        ("three_numbers()",         f"{number}({sep}{number}){{2}}"),
        ("three_mixed_number()",    f"{mixed_number}({sep}{mixed_number}){{2}}"),
        ("three_mixed_numbers()",   f"{mixed_number}({sep}{mixed_number}){{2}}"),
    ]
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected

@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_digit()",         f"{digit}{{{2},{5}}}"),
        ("two_to_five_digits()",        f"{digit}{{{2},{5}}}"),
        ("two_to_five_number()",        f"{number}({sep}{number}){{{1},{4}}}"),
        ("two_to_five_numbers()",       f"{number}({sep}{number}){{{1},{4}}}"),
        ("two_to_five_mixed_number()",  f"{mixed_number}({sep}{mixed_number}){{{1},{4}}}"),
        ("two_to_five_mixed_numbers()", f"{mixed_number}({sep}{mixed_number}){{{1},{4}}}"),
    ]
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected
