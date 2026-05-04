"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_exact_quantity_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_exact_quantity_mapping.py
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
        ("3_dot",               rf"{dot}{{3}}"),
        ("three_dot",           rf"{dot}{{3}}"),
        ("3dot",                rf"{dot}{{3}}"),
        ("fortyfive_dot",       rf"{dot}{{45}}"),

        # --- Literal spaces ---
        ("3_space",             rf"{space}{{3}}"),
        ("3_spaces",            rf"{space}{{3}}"),

        # --- Whitespace ---
        ("three_ws",            rf"{ws}{{3}}"),
        ("3_whitespace",        rf"{ws}{{3}}"),
        ("3_wss",               rf"{ws}{{3}}"),


        # --- Digits ---
        ("3_digit",             rf"{digit}{{3}}"),
        ("3digit",              rf"{digit}{{3}}"),
        ("3_digits",            rf"{digit}{{3}}"),


        # --- Number ---
        ("3_number",            rf"{number}({sep}{number}){{2}}"),
        ("3_mixed_number",      rf"{mixed_number}({sep}{mixed_number}){{2}}"),

        # --- letters ---
        ("3_letter",            rf"{letter}{{3}}"),
        ("3_letters",           rf"{letter}{{3}}"),

        # --- alphabet numeric ---
        ("3_alnum",             rf"{alnum}{{3}}"),

        # --- graph ---
        ("3_graph",             rf"{graph}{{3}}"),

        # --- punctuations ---
        ("3_punct",             rf"{punct}{{3}}"),
        ("3_puncts",            rf"{punct}{{3}}"),

        # --- space or punctuation ---
        ("3_space_or_punct",    rf"{space_or_punct}{{3}}"),

        # --- letter or punctuation ---
        ("3_letter_or_punct",   rf"{letter_or_punct}{{3}}"),

        # --- word ---
        ("3_word",              rf"{word}({sep}{word}){{2}}"),
        ("3_words",             rf"{word}({sep}{word}){{2}}"),

        # --- mixed-word ---
        ("3_mixed_word",        rf"{mixed_word}({sep}{mixed_word}){{2}}"),
        ("3_mixed_words",       rf"{mixed_word}({sep}{mixed_word}){{2}}"),

        # --- non-whitespace(s) ---
        ("3_non_ws",            rf"{non_ws}{{3}}"),
        ("3_non_wss",           rf"{non_ws}{{3}}"),

        ("3_non_ws_group",      rf"{non_wss}({sep}{non_wss}){{2}}"),
        ("3_non_wss_group",     rf"{non_wss}({sep}{non_wss}){{2}}"),

    ]
)
def test(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # dot
        ("4_dot_group",             rf"{dot}{{4}}"),
        ("four_dot_group",          rf"{dot}{{4}}"),

        # dots
        ("4_dots_group",            rf"{dot}{{4}}"),
        ("four_dots_group",         rf"{dot}{{4}}"),

        # space
        ("4_space_group",           rf"{space}{{4}}"),
        ("four_space_group",        rf"{space}{{4}}"),

        # spaces
        ("4_spaces_group",          rf"{space}{{4}}"),
        ("four_spaces_group",       rf"{space}{{4}}"),

        # ws
        ("4_ws_group",              rf"{ws}{{4}}"),
        ("four_ws_group",           rf"{ws}{{4}}"),

        # wss
        ("4_wss_group",             rf"{ws}{{4}}"),
        ("four_wss_group",          rf"{ws}{{4}}"),

        # whitespace
        ("4_whitespace_group",      rf"{ws}{{4}}"),
        ("four_whitespace_group",   rf"{ws}{{4}}"),

        # whitespaces
        ("4_whitespaces_group",     rf"{ws}{{4}}"),
        ("four_whitespaces_group",  rf"{ws}{{4}}"),
    ]
)
def test_special_case_suppressible_group(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected