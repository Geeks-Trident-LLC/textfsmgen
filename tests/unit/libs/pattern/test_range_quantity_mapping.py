"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_range_quantity_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_range_quantity_mapping.py
"""

import pytest

from textfsmgen.libs.pattern import ParsedKeywordMappingName

from tests.unit.libs.pattern import (
    space,
    ws,
    wss,  # noqa
    dot,
    letter,
    letters,  # noqa
    graph,  # noqa
    puncts,  # noqa
    number,
    mixed_number,
    word,
    mixed_word,  # noqa
    letter_or_punct,  # noqa
    sep,
)


@pytest.mark.parametrize(
    "name, expected",
    [
        # test singular char
        ("1_3_letter", rf"{letter}{{1,3}}"),
        ("one_3_letter", rf"{letter}{{1,3}}"),
        ("one_three_letter", rf"{letter}{{1,3}}"),
        ("one_to_three_letter", rf"{letter}{{1,3}}"),
        ("one_to_3_letter", rf"{letter}{{1,3}}"),
        ("1_to_3_letter", rf"{letter}{{1,3}}"),
        ("_3_letter", rf"{letter}{{,3}}"),
        ("_three_letter", rf"{letter}{{,3}}"),
        ("_to_three_letter", rf"{letter}{{,3}}"),
        ("_to_3_letter", rf"{letter}{{,3}}"),
        ("2__letter", rf"{letter}{{2,}}"),
        ("two__letter", rf"{letter}{{2,}}"),
        ("two_to__letter", rf"{letter}{{2,}}"),
        ("0_3_letter", rf"{letter}{{,3}}"),
    ],
)
def test_single_char_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # test multiple chars
        ("1_3_letters", rf"{letter}{{1,3}}"),
        ("one_3_letters", rf"{letter}{{1,3}}"),
        ("one_three_letters", rf"{letter}{{1,3}}"),
        ("one_to_three_letters", rf"{letter}{{1,3}}"),
        ("one_to_3_letters", rf"{letter}{{1,3}}"),
        ("1_to_3_letters", rf"{letter}{{1,3}}"),
        #
        ("_3_letters", rf"{letter}{{,3}}"),
        ("_three_letters", rf"{letter}{{,3}}"),
        ("_to_three_letters", rf"{letter}{{,3}}"),
        ("_to_3_letters", rf"{letter}{{,3}}"),
        ("2__letters", rf"{letter}{{2,}}"),
        ("two__letters", rf"{letter}{{2,}}"),
        ("two_to__letters", rf"{letter}{{2,}}"),
        ("1__letters", rf"{letter}{{1,}}"),
        ("one__letters", rf"{letter}{{1,}}"),
        ("one_to__letters", rf"{letter}{{1,}}"),
        ("0_3_letters", rf"{letter}{{,3}}"),
        ("2_5_letters", rf"{letter}{{2,5}}"),
    ],
)
def test_range_multiple_chars_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # test semantic: word
        ("0_to_4_word", rf"({word}({sep}{word}){{,3}})?"),
        ("zero_to_four_word", rf"({word}({sep}{word}){{,3}})?"),
        ("2_to_4_word", rf"{word}({sep}{word}){{1,3}}"),
        ("two_to_four_word", rf"{word}({sep}{word}){{1,3}}"),
        ("2_to_4_mixed_word", rf"{mixed_word}({sep}{mixed_word}){{1,3}}"),
        ("two_to_four_mixed_word", rf"{mixed_word}({sep}{mixed_word}){{1,3}}"),
        ("2_to_4_number", rf"{number}({sep}{number}){{1,3}}"),
        ("two_to_four_number", rf"{number}({sep}{number}){{1,3}}"),
        ("2_to_4_mixed_number", rf"{mixed_number}({sep}{mixed_number}){{1,3}}"),
        ("two_to_four_mixed_number", rf"{mixed_number}({sep}{mixed_number}){{1,3}}"),
    ],
)
def test(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # dot
        ("0_to_4_dot_group", rf"{dot}{{,4}}"),
        ("zero_to_four_dot_group", rf"{dot}{{,4}}"),
        ("2_to_4_dot_group", rf"{dot}{{2,4}}"),
        ("two_to_four_dot_group", rf"{dot}{{2,4}}"),
        # dots
        ("0_to_4_dots_group", rf"{dot}{{,4}}"),
        ("zero_to_four_dots_group", rf"{dot}{{,4}}"),
        ("2_to_4_dots_group", rf"{dot}{{2,4}}"),
        ("two_to_four_dots_group", rf"{dot}{{2,4}}"),
        # space
        ("0_to_4_space_group", rf"{space}{{,4}}"),
        ("zero_to_four_space_group", rf"{space}{{,4}}"),
        ("2_to_4_space_group", rf"{space}{{2,4}}"),
        ("two_to_four_space_group", rf"{space}{{2,4}}"),
        # spaces
        ("0_to_4_spaces_group", rf"{space}{{,4}}"),
        ("zero_to_four_spaces_group", rf"{space}{{,4}}"),
        ("2_to_4_spaces_group", rf"{space}{{2,4}}"),
        ("two_to_four_spaces_group", rf"{space}{{2,4}}"),
        # ws
        ("0_to_4_ws_group", rf"{ws}{{,4}}"),
        ("zero_to_four_ws_group", rf"{ws}{{,4}}"),
        ("2_to_4_ws_group", rf"{ws}{{2,4}}"),
        ("two_to_four_ws_group", rf"{ws}{{2,4}}"),
        # wss
        ("0_to_4_wss_group", rf"{ws}{{,4}}"),
        ("zero_to_four_wss_group", rf"{ws}{{,4}}"),
        ("2_to_4_wss_group", rf"{ws}{{2,4}}"),
        ("two_to_four_wss_group", rf"{ws}{{2,4}}"),
        # whitespace
        ("0_to_4_whitespace_group", rf"{ws}{{,4}}"),
        ("zero_to_four_whitespace_group", rf"{ws}{{,4}}"),
        ("2_to_4_whitespace_group", rf"{ws}{{2,4}}"),
        ("two_to_four_whitespace_group", rf"{ws}{{2,4}}"),
        # whitespaces
        ("0_to_4_whitespaces_group", rf"{ws}{{,4}}"),
        ("zero_to_four_whitespaces_group", rf"{ws}{{,4}}"),
        ("2_to_4_whitespaces_group", rf"{ws}{{2,4}}"),
        ("two_to_four_whitespaces_group", rf"{ws}{{2,4}}"),
    ],
)
def test_special_case_suppressible_group(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected
