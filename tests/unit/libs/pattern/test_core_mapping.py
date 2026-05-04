"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_core_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_core_mapping.py
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
        ("dot",                         rf"{dot}"),
        ("dots",                        rf"{dot}+"),
        ("anything",                    rf"{dot}*"),
        ("something",                   rf"{dot}+"),

        # --- Literal spaces ---
        ("space",                       rf"{space}"),
        ("spaces",                      rf"{space}+"),

        # --- Whitespace ---
        ("ws",                          rf"{ws}"),
        ("wss",                         rf"{wss}"),
        ("whitespace",                  rf"{ws}"),
        ("whitespaces",                 rf"{ws}+"),

        # --- Digits ---
        ("digit",                       rf"{digit}"),
        ("digits",                      rf"{digit}+"),

        # --- Number ---
        ("number",                      rf"{number}"),
        ("mixed_number",                rf"{mixed_number}"),
        ("numbers",                     rf"{number}({sep}{number})*"),
        ("mixed_numbers",               rf"{mixed_number}({sep}{mixed_number})*"),

        # --- letters ---
        ("letter",                      rf"{letter}"),
        ("letters",                     rf"{letters}"),

        # --- alphabet numeric ---
        ("alnum",                       rf"{alnum}"),
        ("alnums",                      rf"{alnum}+"),

        # --- graph ---
        ("graph",                       rf"{graph}"),
        ("graphs",                      rf"{graph}+"),

        # --- punctuations ---
        ("punct",                       rf"{punct}"),
        ("puncts",                      rf"{punct}+"),

        # --- space or punctuation ---
        ("space_or_punct",              rf"{space_or_punct}"),

        # --- letter or punctuation ---
        ("letter_or_punct",             rf"{letter_or_punct}"),

        # --- word ---
        ("word",                        rf"{word}"),
        ("words",                       rf"{word}({sep}{word})*"),

        # --- mixed-word ---
        ("mixed_word",                  rf"{mixed_word}"),
        ("mixed_words",                 rf"{mixed_word}({sep}{mixed_word})*"),

        # --- non-whitespace(s) ---
        ("non_ws",                      rf"{non_ws}"),
        ("non_wss",                     rf"{non_ws}+"),
    ]
)
def test(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected
