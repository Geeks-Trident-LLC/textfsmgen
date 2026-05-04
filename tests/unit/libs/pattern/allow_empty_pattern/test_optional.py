"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_optional.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_optional.py
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
        # Name                          Pattern                     Expected
        # Generic wildcard
        ("optional_dot", rf"{dot}?", rf"{dot}?"),
        ("optional_dots", rf"{dot}*", rf"{dot}*"),
        # Literal spaces
        ("optional_space", rf"{space}?", rf"{space}?"),
        ("optional_spaces", rf"{space}*", rf"{space}*"),
        # --- Whitespace ---
        ("optional_ws", rf"{ws}?", rf"{ws}?"),
        ("optional_wss", rf"{ws}*", rf"{ws}*"),
        ("optional_whitespace", rf"{ws}?", rf"{ws}?"),
        ("optional_whitespaces", rf"{ws}*", rf"{ws}*"),
        # --- Digits ---
        ("optional_digit", rf"{digit}?", rf"{digit}?"),
        ("optional_digits", rf"{digit}*", rf"{digit}*"),
        # --- Number ---
        ("optional_number", rf"({number})?", rf"({number})?"),
        (
            "optional_mixed_number",
            rf"({mixed_number})?",
            rf"({mixed_number})?",
        ),
        (
            "optional_numbers",
            rf"({number}({sep}{number})*)?",
            rf"({number}({sep}{number})*)?",
        ),
        (
            "optional_mixed_numbers",
            rf"({mixed_number}({sep}{mixed_number})*)?",
            rf"({mixed_number}({sep}{mixed_number})*)?",
        ),
        # # --- letters ---
        ("optional_letter", rf"{letter}?", rf"{letter}?"),
        ("optional_letters", rf"{letter}*", rf"{letter}*"),
        #
        # # --- alnum ---
        ("optional_alnum", rf"{alnum}?", rf"{alnum}?"),
        ("optional_alnums", rf"{alnum}*", rf"{alnum}*"),
        # --- graph ---
        ("optional_graph", rf"{graph}?", rf"{graph}?"),
        ("optional_graphs", rf"{graph}*", rf"{graph}*"),
        #
        # # --- punct ---
        ("optional_punct", rf"{punct}?", rf"{punct}?"),
        ("optional_puncts", rf"{punct}*", rf"{punct}*"),
        # space or punct
        ("optional_space_or_punct", rf"{space_or_punct}?", rf"{space_or_punct}?"),
        # letter or punct
        ("optional_letter_or_punct", rf"{letter_or_punct}?", rf"{letter_or_punct}?"),
        # --- word ---
        ("optional_word", rf"({word})?", rf"({word})?"),
        ("optional_words", rf"({word}({sep}{word})*)?", rf"({word}({sep}{word})*)?"),
        # --- mixed-word
        ("optional_mixed_word", rf"({mixed_word})?", rf"({mixed_word})?"),
        (
            "optional_mixed_words",
            rf"({mixed_word}({sep}{mixed_word})*)?",
            rf"({mixed_word}({sep}{mixed_word})*)?",
        ),
        # non-whitespace(s)
        ("optional_non_ws", rf"{non_ws}?", rf"{non_ws}?"),
        ("optional_non_wss", rf"{non_ws}*", rf"{non_ws}*"),
    ],
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern

    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
