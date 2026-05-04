"""
Unit tests for the `textfsmgen.core.patterns.ElementPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/element_pattern/test_word.py
    or
    $ python -m pytest tests/unit/core/element_pattern/test_word.py
"""

import pytest

from textfsmgen.core.patterns import ElementPattern


from tests.unit.libs.pattern import (
    wss,  # noqa
    letter,
    letters,  # noqa
    graph,  # noqa
    puncts,  # noqa
    word,
    mixed_word,  # noqa
    letter_or_punct,  # noqa
    alnum,
    alnums,  # noqa
    sep,
)


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("letter()", f"{letter}"),
        ("letters()", f"{letter}+"),
        ("alnum()", f"{alnum}"),
        ("alnums()", f"{alnum}+"),
        ("word()", f"{word}"),
        ("words()", f"{word}({sep}{word})*"),
        ("mixed_word()", f"{mixed_word}"),
        ("mixed_words()", f"{mixed_word}({sep}{mixed_word})*"),
    ],
)
def test(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("optional_letter()", f"{letter}?"),
        ("optional_letters()", f"{letter}*"),
        ("optional_alnum()", f"{alnum}?"),
        ("optional_alnums()", f"{alnum}*"),
        ("optional_word()", f"({word})?"),
        ("optional_words()", f"({word}({sep}{word})*)?"),
        ("optional_mixed_word()", f"({mixed_word})?"),
        ("optional_mixed_words()", f"({mixed_word}({sep}{mixed_word})*)?"),
    ],
)
def test_optional(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_one_letter()", f"{letter}?"),
        ("zero_or_one_letters()", f"{letter}*"),
        ("zero_or_one_alnum()", f"{alnum}?"),
        ("zero_or_one_alnums()", f"{alnum}*"),
        ("zero_or_one_word()", f"({word})?"),
        ("zero_or_one_words()", f"({word}({sep}{word})*)?"),
        ("zero_or_one_mixed_word()", f"({mixed_word})?"),
        ("zero_or_one_mixed_words()", f"({mixed_word}({sep}{mixed_word})*)?"),
    ],
)
def test_zero_or_one(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("zero_or_more_letter()", f"{letter}*"),
        ("zero_or_more_letters()", f"{letter}*"),
        ("zero_or_more_alnum()", f"{alnum}*"),
        ("zero_or_more_alnums()", f"{alnum}*"),
        ("zero_or_more_word()", f"({word}({sep}{word})*)?"),
        ("zero_or_more_words()", f"({word}({sep}{word})*)?"),
        ("zero_or_more_mixed_word()", f"({mixed_word}({sep}{mixed_word})*)?"),
        ("zero_or_more_mixed_words()", f"({mixed_word}({sep}{mixed_word})*)?"),
    ],
)
def test_zero_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("one_or_more_letter()", f"{letter}+"),
        ("one_or_more_letters()", f"{letter}+"),
        ("one_or_more_alnum()", f"{alnum}+"),
        ("one_or_more_alnums()", f"{alnum}+"),
        ("one_or_more_word()", f"{word}({sep}{word})*"),
        ("one_or_more_words()", f"{word}({sep}{word})*"),
        ("one_or_more_mixed_word()", f"{mixed_word}({sep}{mixed_word})*"),
        ("one_or_more_mixed_words()", f"{mixed_word}({sep}{mixed_word})*"),
    ],
)
def test_one_or_more(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("letter_group()", f"{letters}({sep}{letters})+"),
        ("letters_group()", f"{letters}({sep}{letters})+"),
        ("alnum_group()", f"{alnums}({sep}{alnums})+"),
        ("alnums_group()", f"{alnums}({sep}{alnums})+"),
        ("word_group()", f"{word}({sep}{word})+"),
        ("words_group()", f"{word}({sep}{word})+"),
        ("mixed_word_group()", f"{mixed_word}({sep}{mixed_word})+"),
        ("mixed_words_group()", f"{mixed_word}({sep}{mixed_word})+"),
        ("optional_letter_group()", f"({letters}({sep}{letters})+)?"),
        ("optional_letters_group()", f"({letters}({sep}{letters})+)?"),
        ("optional_alnum_group()", f"({alnums}({sep}{alnums})+)?"),
        ("optional_alnums_group()", f"({alnums}({sep}{alnums})+)?"),
        ("optional_word_group()", f"({word}({sep}{word})+)?"),
        ("optional_words_group()", f"({word}({sep}{word})+)?"),
        ("optional_mixed_word_group()", f"({mixed_word}({sep}{mixed_word})+)?"),
        ("optional_mixed_words_group()", f"({mixed_word}({sep}{mixed_word})+)?"),
        ("letter_items()", f"{letters}({sep}{letters})*"),
        ("letters_items()", f"{letters}({sep}{letters})*"),
        ("alnum_items()", f"{alnums}({sep}{alnums})*"),
        ("alnums_items()", f"{alnums}({sep}{alnums})*"),
        ("word_items()", f"{word}({sep}{word})*"),
        ("words_items()", f"{word}({sep}{word})*"),
        ("mixed_word_items()", f"{mixed_word}({sep}{mixed_word})*"),
        ("mixed_words_items()", f"{mixed_word}({sep}{mixed_word})*"),
        ("optional_letter_items()", f"({letters}({sep}{letters})*)?"),
        ("optional_letters_items()", f"({letters}({sep}{letters})*)?"),
        ("optional_alnum_items()", f"({alnums}({sep}{alnums})*)?"),
        ("optional_alnums_items()", f"({alnums}({sep}{alnums})*)?"),
        ("optional_word_items()", f"({word}({sep}{word})*)?"),
        ("optional_words_items()", f"({word}({sep}{word})*)?"),
        ("optional_mixed_word_items()", f"({mixed_word}({sep}{mixed_word})*)?"),
        ("optional_mixed_words_items()", f"({mixed_word}({sep}{mixed_word})*)?"),
    ],
)
def test_group(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("three_letter()", f"{letter}{{3}}"),
        ("three_letters()", f"{letter}{{3}}"),
        ("three_alnum()", f"{alnum}{{3}}"),
        ("three_alnums()", f"{alnum}{{3}}"),
        ("three_word()", f"{word}({sep}{word}){{2}}"),
        ("three_words()", f"{word}({sep}{word}){{2}}"),
        ("three_mixed_word()", f"{mixed_word}({sep}{mixed_word}){{2}}"),
        ("three_mixed_words()", f"{mixed_word}({sep}{mixed_word}){{2}}"),
    ],
)
def test_exact_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected


@pytest.mark.parametrize(
    "snippet, expected",
    [
        ("two_to_five_letter()", f"{letter}{{{2},{5}}}"),
        ("two_to_five_letters()", f"{letter}{{{2},{5}}}"),
        ("two_to_five_alnum()", f"{alnum}{{{2},{5}}}"),
        ("two_to_five_alnums()", f"{alnum}{{{2},{5}}}"),
        ("two_to_five_word()", f"{word}({sep}{word}){{{1},{4}}}"),
        ("two_to_five_words()", f"{word}({sep}{word}){{{1},{4}}}"),
        ("two_to_five_mixed_word()", f"{mixed_word}({sep}{mixed_word}){{{1},{4}}}"),
        ("two_to_five_mixed_words()", f"{mixed_word}({sep}{mixed_word}){{{1},{4}}}"),
    ],
)
def test_range_match(snippet, expected):
    node = ElementPattern(snippet)
    assert node == expected
