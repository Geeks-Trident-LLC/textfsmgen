"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_group_quantity_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_group_quantity_mapping.py
"""

import pytest

from textfsmgen.libs.pattern import ParsedKeywordMappingName

from tests.unit.libs.pattern import (
    space, spaces, ws, wss,                     # noqa
    dot, letter, letters,                       # noqa
    digit, digits, alnum, graph,                # noqa
    non_ws, non_wss, punct, puncts,             # noqa
    number, mixed_number, word, mixed_word,     # noqa
    space_or_punct, letter_or_punct,            # noqa

    sep
)


@pytest.mark.parametrize(
    "name, expected",
    [
        # --- Generic wildcard ---
        ("dot_group",                   rf"{dot}+"),
        ("dots_group",                  rf"{dot}+"),
        #
        # # --- Literal spaces ---
        ("space_group",                 rf"{spaces}"),
        ("spaces_group",                rf"{spaces}"),
        #
        # # --- Whitespace ---
        ("ws_group",                    rf"{wss}"),
        ("wss_group",                   rf"{wss}"),
        ("whitespace_group",            rf"{wss}"),
        ("whitespaces_group",           rf"{wss}"),

        # --- Digits ---
        ("digit_group",                 rf"{digits}({sep}{digits})+"),
        ("digits_group",                rf"{digits}({sep}{digits})+"),

        # --- Number ---
        ("number_group",                rf"{number}({sep}{number})+"),
        ("mixed_number_group",          rf"{mixed_number}({sep}{mixed_number})+"),
        ("numbers_group",               rf"{number}({sep}{number})+"),
        ("mixed_numbers_group",         rf"{mixed_number}({sep}{mixed_number})+"),

        # --- letters ---
        ("letter_group",                rf"{letters}({sep}{letters})+"),
        ("letters_group",               rf"{letters}({sep}{letters})+"),

        # --- alphabet numeric ---
        ("alnum",                       rf"{alnum}"),
        ("alnums",                      rf"{alnum}+"),

        # --- graph ---
        ("graph_group",                 rf"{graph}+({sep}{graph}+)+"),
        ("graphs_group",                rf"{graph}+({sep}{graph}+)+"),

        # --- punctuations ---
        ("punct_group",                 rf"{puncts}({sep}{puncts})+"),
        ("puncts_group",                rf"{puncts}({sep}{puncts})+"),
        ("puncts_group",                rf"{puncts}({sep}{puncts})+"),

        # --- space or punctuation ---
        ("space_or_punct_group",        rf"{space_or_punct}+({sep}{space_or_punct}+)+"),

        # --- letter or punctuation ---
        ("letter_or_punct_group",       rf"{letter_or_punct}+({sep}{letter_or_punct}+)+"),

        # --- word ---
        ("word_group",                  rf"{word}({sep}{word})+"),
        ("words_group",                 rf"{word}({sep}{word})+"),

        # --- mixed-word ---
        ("mixed_word_group",            rf"{mixed_word}({sep}{mixed_word})+"),
        ("mixed_words_group",           rf"{mixed_word}({sep}{mixed_word})+"),

        # --- non-whitespace(s) ---
        ("non_ws_group",                rf"{non_wss}({sep}{non_wss})+"),
        ("non_wss_group",               rf"{non_wss}({sep}{non_wss})+"),
    ]
)
def test(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected
