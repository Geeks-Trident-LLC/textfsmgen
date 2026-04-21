"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_zero_or_one.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_zero_or_one.py
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
    spaces_or_puncts, letters_or_puncts,            # noqa

    sep
)



@pytest.mark.parametrize(
    "name, pattern, expected",
    [
        # Name                             Pattern                     Expected
        # --- Generic wildcard ---
        ("zero_or_one_dot",                rf"{dot}?",                 rf"{dot}?"),
        ("zero_or_one_dots",               rf"{dot}*",                 rf"{dot}*"),

        # --- Literal spaces ---
        ("zero_or_one_space",              rf"{space}?",               rf"{space}?" ),
        ("zero_or_one_spaces",             rf"{space}*",               rf"{space}*"),

        # --- Whitespace ---
        ("zero_or_one_ws",                 rf"{ws}?",                  rf"{ws}?"),
        ("zero_or_one_wss",                rf"{ws}*",                  rf"{ws}*"),
        ("zero_or_one_whitespace",         rf"{ws}?",                  rf"{ws}?"),
        ("zero_or_one_whitespaces",        rf"{ws}*",                  rf"{ws}*"),

        # --- Digits ---
        ("zero_or_one_digit",              rf"{digit}?",               rf"{digit}?"),
        ("zero_or_one_digits",             rf"{digit}*",               rf"{digit}*"),

        # --- Number ---
        ("zero_or_one_number",             rf"({number})?",               rf"({number})?"),
        ("zero_or_one_mixed_number",       rf"({mixed_number})?",         rf"({mixed_number})?",),
        ("zero_or_one_numbers",            rf"({number}({sep}{number})*)?",               rf"({number}({sep}{number})*)?"),
        ("zero_or_one_mixed_numbers",      rf"({mixed_number}({sep}{mixed_number})*)?",   rf"({mixed_number}({sep}{mixed_number})*)?"),

        # # --- letters ---
        ("zero_or_one_letter",             rf"{letter}?",              rf"{letter}?"),
        ("zero_or_one_letters",            rf"{letter}*",              rf"{letter}*"),
        #
        # # --- alnum ---
        ("zero_or_one_alnum",              rf"{alnum}?",               rf"{alnum}?"),
        ("zero_or_one_alnums",             rf"{alnum}*" ,              rf"{alnum}*"),

        # --- graph ---
        ("zero_or_one_graph",              rf"{graph}?",               rf"{graph}?"),
        ("zero_or_one_graphs",             rf"{graph}*",               rf"{graph}*"),
        #
        # --- punct ---
        ("zero_or_one_punct",              rf"{punct}?",               rf"{punct}?"),
        ("zero_or_one_puncts",             rf"{punct}*",               rf"{punct}*"),

        # --- space or punct ---
        ("zero_or_one_space_or_punct",     rf"{space_or_punct}?",      rf"{space_or_punct}?"),

        # --- letter or punct ---
        ("zero_or_one_letter_or_punct",    rf"{letter_or_punct}?",     rf"{letter_or_punct}?"),

        # --- word ---
        ("zero_or_one_word",               rf"({word})?",                 rf"({word})?"),
        ("zero_or_one_words",              rf"({word}({sep}{word})*)?",   rf"({word}({sep}{word})*)?"),

        # --- mixed-word
        ("zero_or_one_mixed_word",         rf"({mixed_word})?",                       rf"({mixed_word})?"),
        ("zero_or_one_mixed_words",        rf"({mixed_word}({sep}{mixed_word})*)?",   rf"({mixed_word}({sep}{mixed_word})*)?"),

        # non-whitespace(s)
        ("zero_or_one_non_ws",             rf"{non_ws}?",               rf"{non_ws}?"),
        ("zero_or_one_non_wss",            rf"{non_ws}*",               rf"{non_ws}*"),
    ]
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern

    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
