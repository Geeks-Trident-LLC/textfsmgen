"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_optional_group.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_optional_group.py
"""

import pytest   # noqa

from textfsmgen.libs.pattern import ParsedKeywordMappingName

from textfsmgen.libs.pattern import PATTERN

from tests.unit.libs.pattern import (
    space, spaces, ws, wss,                         # noqa
    dot, letter, letters,                           # noqa
    digit, digits, alnum, alnums, graph, graphs,    # noqa
    non_ws, non_wss, punct, puncts,                 # noqa
    number, mixed_number, word, mixed_word,         # noqa
    space_or_punct, letter_or_punct,                # noqa
    spaces_or_puncts, letters_or_puncts,             # noqa

    sep
)



@pytest.mark.parametrize(
    "name, pattern, expected",
    [
        # Name                                Pattern                     Expected
        # Generic wildcard
        ("optional_dot_group",                rf"{dot}*",                 rf"{dot}*"),
        ("optional_dots_group",               rf"{dot}*",                 rf"{dot}*"),

        # Literal spaces
        ("optional_space_group",              rf"{space}*",               rf"{space}*" ),
        ("optional_spaces_group",             rf"{space}*",               rf"{space}*"),

        # --- Whitespace ---
        ("optional_ws_group",                 rf"{ws}*",                  rf"{ws}*"),
        ("optional_wss_group",                rf"{ws}*",                  rf"{ws}*"),
        ("optional_whitespace_group",         rf"{ws}*",                  rf"{ws}*"),
        ("optional_whitespaces_group",        rf"{ws}*",                  rf"{ws}*"),

        # --- Digits ---
        ("optional_digit_group",              rf"{digits}({sep}{digits})*",               rf"({digits}({sep}{digits})*)?"),
        ("optional_digits_group",             rf"{digits}({sep}{digits})*",               rf"({digits}({sep}{digits})*)?"),

        # --- Number ---
        ("optional_number_group",             rf"{number}({sep}{number})*",               rf"({number}({sep}{number})*)?"),
        ("optional_mixed_number_group",       rf"{mixed_number}({sep}{mixed_number})*",   rf"({mixed_number}({sep}{mixed_number})*)?"),
        ("optional_numbers_group",            rf"{number}({sep}{number})*",               rf"({number}({sep}{number})*)?"),
        ("optional_mixed_numbers_group",      rf"{mixed_number}({sep}{mixed_number})*",   rf"({mixed_number}({sep}{mixed_number})*)?"),

        # # --- letters ---
        ("optional_letter_group",             rf"{letters}({sep}{letters})*",              rf"({letters}({sep}{letters})*)?"),
        ("optional_letters_group",            rf"{letters}({sep}{letters})*",              rf"({letters}({sep}{letters})*)?"),
        #
        # # --- alnum ---
        ("optional_alnum_group",              rf"{alnums}({sep}{alnums})*",                rf"({alnums}({sep}{alnums})*)?"),
        ("optional_alnums_group",             rf"{alnums}({sep}{alnums})*",                rf"({alnums}({sep}{alnums})*)?"),

        # --- graph ---
        ("optional_graph_group",              rf"{graphs}({sep}{graphs})*",                rf"({graphs}({sep}{graphs})*)?"),
        ("optional_graphs_group",             rf"{graphs}({sep}{graphs})*",                rf"({graphs}({sep}{graphs})*)?"),
        #
        # # --- punct ---
        ("optional_punct_group",              rf"{puncts}({sep}{puncts})*",                rf"({puncts}({sep}{puncts})*)?"),
        ("optional_puncts_group",             rf"{puncts}({sep}{puncts})*",                rf"({puncts}({sep}{puncts})*)?"),

        # space or punct
        ("optional_space_or_punct_group",     rf"{spaces_or_puncts}({sep}{spaces_or_puncts})*",      rf"({spaces_or_puncts}({sep}{spaces_or_puncts})*)?"),

        # letter or punct
        ("optional_letter_or_punct_group",    rf"{letters_or_puncts}({sep}{letters_or_puncts})*",    rf"({letters_or_puncts}({sep}{letters_or_puncts})*)?"),

        # --- word ---
        ("optional_word_group",               rf"{word}({sep}{word})*",   rf"({word}({sep}{word})*)?"),
        ("optional_words_group",              rf"{word}({sep}{word})*",   rf"({word}({sep}{word})*)?"),

        # --- mixed-word
        ("optional_mixed_word_group",         rf"{mixed_word}({sep}{mixed_word})*",     rf"({mixed_word}({sep}{mixed_word})*)?"),
        ("optional_mixed_words_group",        rf"{mixed_word}({sep}{mixed_word})*",     rf"({mixed_word}({sep}{mixed_word})*)?"),

        # non-whitespace(s)
        ("optional_non_ws_group",             rf"{non_wss}({sep}{non_wss})*",       rf"({non_wss}({sep}{non_wss})*)?"),
        ("optional_non_wss_group",            rf"{non_wss}({sep}{non_wss})*",       rf"({non_wss}({sep}{non_wss})*)?"),
    ]
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern
    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
