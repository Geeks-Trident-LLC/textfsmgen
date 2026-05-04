"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_one_or_more.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_one_or_more.py
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
    spaces_or_puncts, letters_or_puncts,            # noqa

    sep
)



@pytest.mark.parametrize(
    "name, pattern, expected",
    [
        # Name                  Pattern                     Expected
        # Generic wildcard
        ("one_or_more_dot",                 rf"{dot}+",                 rf"{dot}*"),
        ("one_or_more_dots",                rf"{dot}+",                 rf"{dot}*"),

        # Literal spaces
        ("one_or_more_space",               rf"{space}+",               rf"{space}*" ),
        ("one_or_more_spaces",              rf"{space}+",               rf"{space}*"),

        # --- Whitespace ---
        ("one_or_more_ws",                  rf"{ws}+",                  rf"{ws}*"),
        ("one_or_more_wss",                 rf"{ws}+",                  rf"{ws}*"),
        ("one_or_more_whitespace",          rf"{ws}+",                  rf"{ws}*"),
        ("one_or_more_whitespaces",         rf"{ws}+",                  rf"{ws}*"),

        # --- Digits ---
        ("one_or_more_digit",               rf"{digit}+",               rf"{digit}*"),
        ("one_or_more_digits",              rf"{digit}+",               rf"{digit}*"),

        # --- Number ---
        ("one_or_more_number",              rf"{number}({sep}{number})*",               rf"({number}({sep}{number})*)?"),
        ("one_or_more_mixed_number",        rf"{mixed_number}({sep}{mixed_number})*",   rf"({mixed_number}({sep}{mixed_number})*)?"),
        ("one_or_more_numbers",             rf"{number}({sep}{number})*",               rf"({number}({sep}{number})*)?"),
        ("one_or_more_mixed_numbers",       rf"{mixed_number}({sep}{mixed_number})*",   rf"({mixed_number}({sep}{mixed_number})*)?"),

        # --- letters ---
        ("one_or_more_letter",              rf"{letter}+",              rf"{letter}*"),
        ("one_or_more_letters",             rf"{letter}+",              rf"{letter}*"),

        # --- alnum ---
        ("one_or_more_alnum",               rf"{alnum}+",               rf"{alnum}*"),
        ("one_or_more_alnums",              rf"{alnum}+" ,              rf"{alnum}*"),

        # --- graph ---
        ("one_or_more_graph",               rf"{graph}+",               rf"{graph}*"),
        ("one_or_more_graphs",              rf"{graph}+",               rf"{graph}*"),

        # --- punct ---
        ("one_or_more_punct",               rf"{punct}+",               rf"{punct}*"),
        ("one_or_more_puncts",              rf"{punct}+",               rf"{punct}*"),

        # space or punct
        ("one_or_more_space_or_punct",      rf"{space_or_punct}+",       rf"{space_or_punct}*"),

        # letter or punct
        ("one_or_more_letter_or_punct",     rf"{letter_or_punct}+",      rf"{letter_or_punct}*"),

        # --- word ---
        ("one_or_more_word",                rf"{word}({sep}{word})*",   rf"({word}({sep}{word})*)?"),
        ("one_or_more_words",               rf"{word}({sep}{word})*",   rf"({word}({sep}{word})*)?"),

        # --- mixed-word
        ("one_or_more_mixed_word",          rf"{mixed_word}({sep}{mixed_word})*",   rf"({mixed_word}({sep}{mixed_word})*)?"),
        ("one_or_more_mixed_words",         rf"{mixed_word}({sep}{mixed_word})*",   rf"({mixed_word}({sep}{mixed_word})*)?"),

        # non-whitespace(s)
        ("one_or_more_non_ws",              rf"{non_ws}+",              rf"{non_ws}*"),
        ("one_or_more_non_wss",             rf"{non_ws}+",              rf"{non_ws}*"),
    ]
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern

    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
