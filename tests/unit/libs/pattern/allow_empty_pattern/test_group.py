"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_group.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_group.py
"""

import pytest

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
        # Name                       Pattern                     Expected
        # Generic wildcard
        ("dot_group",                rf"{dot}+",                 rf"{dot}*"),
        ("dots_group",               rf"{dot}+",                 rf"{dot}*"),

        # Literal spaces
        ("space_group",              rf"{space}+",               rf"{space}*" ),
        ("spaces_group",             rf"{space}+",               rf"{space}*"),

        # --- Whitespace ---
        ("ws_group",                 rf"{ws}+",                  rf"{ws}*"),
        ("wss_group",                rf"{ws}+",                  rf"{ws}*"),
        ("whitespace_group",         rf"{ws}+",                  rf"{ws}*"),
        ("whitespaces_group",        rf"{ws}+",                  rf"{ws}*"),

        # --- Digits ---
        ("digit_group",              rf"{digits}({sep}{digits})+",               rf"({digits}({sep}{digits})+)?"),
        ("digits_group",             rf"{digits}({sep}{digits})+",               rf"({digits}({sep}{digits})+)?"),

        # --- Number ---
        ("number_group",             rf"{number}({sep}{number})+",               rf"({number}({sep}{number})+)?"),
        ("mixed_number_group",       rf"{mixed_number}({sep}{mixed_number})+",   rf"({mixed_number}({sep}{mixed_number})+)?"),
        ("numbers_group",            rf"{number}({sep}{number})+",               rf"({number}({sep}{number})+)?"),
        ("mixed_numbers_group",      rf"{mixed_number}({sep}{mixed_number})+",   rf"({mixed_number}({sep}{mixed_number})+)?"),

        # # --- letters ---
        ("letter_group",             rf"{letters}({sep}{letters})+",              rf"({letters}({sep}{letters})+)?"),
        ("letters_group",            rf"{letters}({sep}{letters})+",              rf"({letters}({sep}{letters})+)?"),
        #
        # # --- alnum ---
        ("alnum_group",              rf"{alnums}({sep}{alnums})+",                rf"({alnums}({sep}{alnums})+)?"),
        ("alnums_group",             rf"{alnums}({sep}{alnums})+",                rf"({alnums}({sep}{alnums})+)?"),

        # --- graph ---
        ("graph_group",              rf"{graphs}({sep}{graphs})+",                rf"({graphs}({sep}{graphs})+)?"),
        ("graphs_group",             rf"{graphs}({sep}{graphs})+",                rf"({graphs}({sep}{graphs})+)?"),
        #
        # # --- punct ---
        ("punct_group",              rf"{puncts}({sep}{puncts})+",                rf"({puncts}({sep}{puncts})+)?"),
        ("puncts_group",             rf"{puncts}({sep}{puncts})+",                rf"({puncts}({sep}{puncts})+)?"),

        # space or punct
        ("space_or_punct_group",     rf"{spaces_or_puncts}({sep}{spaces_or_puncts})+",      rf"({spaces_or_puncts}({sep}{spaces_or_puncts})+)?"),

        # letter or punct
        ("letter_or_punct_group",    rf"{letters_or_puncts}({sep}{letters_or_puncts})+",    rf"({letters_or_puncts}({sep}{letters_or_puncts})+)?"),

        # --- word ---
        ("word_group",               rf"{word}({sep}{word})+",   rf"({word}({sep}{word})+)?"),
        ("words_group",              rf"{word}({sep}{word})+",   rf"({word}({sep}{word})+)?"),

        # --- mixed-word
        ("mixed_word_group",         rf"{mixed_word}({sep}{mixed_word})+",     rf"({mixed_word}({sep}{mixed_word})+)?"),
        ("mixed_words_group",        rf"{mixed_word}({sep}{mixed_word})+",     rf"({mixed_word}({sep}{mixed_word})+)?"),

        # non-whitespace(s)
        ("non_ws_group",             rf"{non_wss}({sep}{non_wss})+",       rf"({non_wss}({sep}{non_wss})+)?"),
        ("non_wss_group",            rf"{non_wss}({sep}{non_wss})+",       rf"({non_wss}({sep}{non_wss})+)?"),
    ]
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern
    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
