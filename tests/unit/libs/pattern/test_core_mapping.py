"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_core_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_core_mapping.py
"""

import pytest   # noqa

from textfsmgen.libs.pattern import ParsedKeywordMappingName


space = " "
spaces = " +"
ws = r"\s"
wss = r"\s+"

dot = "."
letter = "[a-zA-Z]"
letters = "[a-zA-Z]+"

digit = r"\d"
digits = r"\d+"

alnum = "[a-zA-Z0-9]"
graph = r"[\x21-\x7e]"

non_ws = r"\S"
non_wss = r"\S+"

punct = r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
puncts = f"{punct}+"

number = r"\d*[.]?\d+"
mixed_number = r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*"
word = r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*"
mixed_word = r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*"

space_or_punct = r"[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
letter_or_punct = r"[a-zA-Z\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"

sep = r"\s+"


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
