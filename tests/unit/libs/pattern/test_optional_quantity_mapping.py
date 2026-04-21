"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_optional_quantity_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_optional_quantity_mapping.py
"""

import pytest   # noqa

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
        ("optional_dot",                rf"{dot}?"),
        ("optional_dots",               rf"{dot}*"),
        ("optional_dot_group",          rf"{dot}*"),
        ("optional_dots_group",         rf"{dot}*"),

        # --- Literal spaces ---
        ("optional_space",              rf"{space}?"),
        ("optional_spaces",             rf"{space}*"),
        ("optional_space_group",        rf"{space}*"),
        ("optional_spaces_group",       rf"{space}*"),

        # --- Whitespace ---
        ("optional_ws",                 rf"{ws}?"),
        ("optional_wss",                rf"{ws}*"),
        ("optional_whitespace",         rf"{ws}?"),
        ("optional_whitespaces",        rf"{ws}*"),

        ("optional_ws_group",           rf"{ws}*"),
        ("optional_wss_group",          rf"{ws}*"),
        ("optional_whitespace_group",   rf"{ws}*"),
        ("optional_whitespaces_group",  rf"{ws}*"),

        # --- Digits ---
        ("optional_digit",              rf"{digit}?"),
        ("optional_digits",             rf"{digit}*"),

        # --- Number ---
        ("optional_number",             rf"({number})?"),
        ("optional_mixed_number",       rf"({mixed_number})?"),

        # --- letters ---
        ("optional_letter",             rf"{letter}?"),
        ("optional_letters",            rf"{letter}*"),
        ("optional_letters_group",      rf"{letters}({sep}{letters})*"),

        # --- alphabet numeric ---
        ("optional_alnum",              rf"{alnum}?"),
        ("optional_alnum_group",        rf"{alnum}+({sep}{alnum}+)*"),
        ("optional_alnums_group",       rf"{alnum}+({sep}{alnum}+)*"),

        # --- graph ---
        ("optional_graph",              rf"{graph}?"),

        # --- punctuations ---
        ("optional_punct",              rf"{punct}?"),
        ("optional_puncts",             rf"{punct}*"),
        ("optional_punct_group",        rf"{puncts}({sep}{puncts})*"),
        ("optional_puncts_group",       rf"{puncts}({sep}{puncts})*"),

        # --- space or punctuation ---
        ("optional_space_or_punct",         rf"{space_or_punct}?"),
        ("optional_space_or_punct_group",   rf"{space_or_punct}+({sep}{space_or_punct}+)*"),
        ("optional_spaces_or_puncts_group", rf"{space_or_punct}+({sep}{space_or_punct}+)*"),

        # --- letter or punctuation ---
        ("optional_letter_or_punct",            rf"{letter_or_punct}?"),
        ("optional_letter_or_punct_group",      rf"{letter_or_punct}+({sep}{letter_or_punct}+)*"),
        ("optional_letters_or_puncts_group",    rf"{letter_or_punct}+({sep}{letter_or_punct}+)*"),

        # --- word ---
        ("optional_word",               rf"({word})?"),
        ("optional_words",              rf"({word}({sep}{word})*)?"),
        ("optional_word_group",         rf"{word}({sep}{word})*"),
        ("optional_words_group",        rf"{word}({sep}{word})*"),

        # --- mixed-word ---
        ("optional_mixed_word",         rf"({mixed_word})?"),
        ("optional_mixed_words",        rf"({mixed_word}({sep}{mixed_word})*)?"),
        ("optional_mixed_word_group",   rf"{mixed_word}({sep}{mixed_word})*"),
        ("optional_mixed_words_group",  rf"{mixed_word}({sep}{mixed_word})*"),

        # --- non-whitespace(s) ---
        ("optional_non_ws",             rf"{non_ws}?"),
        ("optional_non_wss",            rf"{non_ws}*"),
        ("optional_non_ws_group",       rf"{non_wss}({sep}{non_wss})*"),
        ("optional_non_wss_group",      rf"{non_wss}({sep}{non_wss})*"),
    ]
)
def test(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected

