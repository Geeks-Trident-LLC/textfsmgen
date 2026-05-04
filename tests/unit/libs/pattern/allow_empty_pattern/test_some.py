"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_some.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_some.py
"""

import pytest

from textfsmgen.libs.pattern import ParsedKeywordMappingName
from textfsmgen.libs.pattern import PATTERN

from tests.unit.libs.pattern import (
    space,
    ws,
    wss,  # noqa
    dot,
    letter,
    letters,  # noqa
    digit,
    alnum,
    graph,
    graphs,  # noqa
    non_ws,
    punct,
    puncts,  # noqa
    number,
    mixed_number,
    word,
    mixed_word,  # noqa
    space_or_punct,
    letter_or_punct,  # noqa
    letters_or_puncts,  # noqa
    sep,
)


@pytest.mark.parametrize(
    "name, pattern, expected",
    [
        # Name                  Pattern                     Expected
        # Generic wildcard
        ("some_dot", rf"{dot}+", rf"{dot}*"),
        ("some_dots", rf"{dot}+", rf"{dot}*"),
        # Literal spaces
        ("some_space", rf"{space}+", rf"{space}*"),
        ("some_spaces", rf"{space}+", rf"{space}*"),
        # --- Whitespace ---
        ("some_ws", rf"{ws}+", rf"{ws}*"),
        ("some_wss", rf"{ws}+", rf"{ws}*"),
        ("some_whitespace", rf"{ws}+", rf"{ws}*"),
        ("some_whitespaces", rf"{ws}+", rf"{ws}*"),
        # --- Digits ---
        ("some_digit", rf"{digit}+", rf"{digit}*"),
        ("some_digits", rf"{digit}+", rf"{digit}*"),
        # --- Number ---
        ("some_number", rf"{number}({sep}{number})*", rf"({number}({sep}{number})*)?"),
        (
            "some_mixed_number",
            rf"{mixed_number}({sep}{mixed_number})*",
            rf"({mixed_number}({sep}{mixed_number})*)?",
        ),
        ("some_numbers", rf"{number}({sep}{number})*", rf"({number}({sep}{number})*)?"),
        (
            "some_mixed_numbers",
            rf"{mixed_number}({sep}{mixed_number})*",
            rf"({mixed_number}({sep}{mixed_number})*)?",
        ),
        # --- letters ---
        ("some_letter", rf"{letter}+", rf"{letter}*"),
        ("some_letters", rf"{letter}+", rf"{letter}*"),
        # --- alnum ---
        ("some_alnum", rf"{alnum}+", rf"{alnum}*"),
        ("some_alnums", rf"{alnum}+", rf"{alnum}*"),
        # --- graph ---
        ("some_graph", rf"{graph}+", rf"{graph}*"),
        ("some_graphs", rf"{graph}+", rf"{graph}*"),
        # --- punct ---
        ("some_punct", rf"{punct}+", rf"{punct}*"),
        ("some_puncts", rf"{punct}+", rf"{punct}*"),
        # space or punct
        ("some_space_or_punct", rf"{space_or_punct}+", rf"{space_or_punct}*"),
        # letter or punct
        ("some_letter_or_punct", rf"{letter_or_punct}+", rf"{letter_or_punct}*"),
        # --- word ---
        ("some_word", rf"{word}({sep}{word})*", rf"({word}({sep}{word})*)?"),
        ("some_words", rf"{word}({sep}{word})*", rf"({word}({sep}{word})*)?"),
        # --- mixed-word
        (
            "some_mixed_word",
            rf"{mixed_word}({sep}{mixed_word})*",
            rf"({mixed_word}({sep}{mixed_word})*)?",
        ),
        (
            "some_mixed_words",
            rf"{mixed_word}({sep}{mixed_word})*",
            rf"({mixed_word}({sep}{mixed_word})*)?",
        ),
        # non-whitespace(s)
        ("some_non_ws", rf"{non_ws}+", rf"{non_ws}*"),
        ("some_non_wss", rf"{non_ws}+", rf"{non_ws}*"),
    ],
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern

    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
