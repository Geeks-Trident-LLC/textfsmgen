"""
Unit tests for the `textfsmgen.libs.pattern.Pattern.allow_empty_pattern` method.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/allow_empty_pattern/test_core.py
    or
    $ python -m pytest tests/unit/libs/pattern/allow_empty_pattern/test_core.py
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
        ("dot", rf"{dot}", rf"{dot}?"),
        ("dots", rf"{dot}+", rf"{dot}*"),
        ("anything", rf"{dot}*", rf"{dot}*"),
        ("something", rf"{dot}+", rf"{dot}*"),
        # Literal spaces
        ("space", rf"{space}", rf"{space}?"),
        ("spaces", rf"{space}+", rf"{space}*"),
        # --- Whitespace ---
        ("ws", rf"{ws}", rf"{ws}?"),
        ("wss", rf"{ws}+", rf"{ws}*"),
        ("whitespace", rf"{ws}", rf"{ws}?"),
        ("whitespaces", rf"{ws}+", rf"{ws}*"),
        # --- Digits ---
        ("digit", rf"{digit}", rf"{digit}?"),
        ("digits", rf"{digit}+", rf"{digit}*"),
        # --- Number ---
        ("number", rf"{number}", rf"({number})?"),
        (
            "mixed_number",
            rf"{mixed_number}",
            rf"({mixed_number})?",
        ),
        ("numbers", rf"{number}({sep}{number})*", rf"({number}({sep}{number})*)?"),
        (
            "mixed_numbers",
            rf"{mixed_number}({sep}{mixed_number})*",
            rf"({mixed_number}({sep}{mixed_number})*)?",
        ),
        # --- letters ---
        ("letter", rf"{letter}", rf"{letter}?"),
        ("letters", rf"{letter}+", rf"{letter}*"),
        # --- alnum ---
        ("alnum", rf"{alnum}", rf"{alnum}?"),
        ("alnums", rf"{alnum}+", rf"{alnum}*"),
        # --- graph ---
        ("graph", rf"{graph}", rf"{graph}?"),
        ("graphs", rf"{graph}+", rf"{graph}*"),
        # --- punct ---
        ("punct", rf"{punct}", rf"{punct}?"),
        ("puncts", rf"{punct}+", rf"{punct}*"),
        # space or punct
        ("space_or_punct", rf"{space_or_punct}", rf"{space_or_punct}?"),
        # letter or punct
        ("letter_or_punct", rf"{letter_or_punct}", rf"{letter_or_punct}?"),
        # --- word ---
        ("word", rf"{word}", rf"({word})?"),
        ("words", rf"{word}({sep}{word})*", rf"({word}({sep}{word})*)?"),
        # --- mixed-word
        ("mixed_word", rf"{mixed_word}", rf"({mixed_word})?"),
        (
            "mixed_words",
            rf"{mixed_word}({sep}{mixed_word})*",
            rf"({mixed_word}({sep}{mixed_word})*)?",
        ),
        # non-whitespace(s)
        ("non_ws", rf"{non_ws}", rf"{non_ws}?"),
        ("non_wss", rf"{non_ws}+", rf"{non_ws}*"),
    ],
)
def test(name, pattern, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == pattern

    allowed_empty_pattern = PATTERN.allow_empty_pattern(pattern)
    assert allowed_empty_pattern == expected
