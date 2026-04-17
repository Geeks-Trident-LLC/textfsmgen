"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_some_quantity_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_some_quantity_mapping.py
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
        ("some_dot",                        rf"{dot}+"),
        ("some_dots",                       rf"{dot}+"),

        # --- Literal spaces ---
        ("some_space",                      rf"{space}+"),
        ("some_spaces",                     rf"{space}+"),

        # --- Whitespace ---
        ("some_ws",                         rf"{ws}+"),
        ("some_wss",                        rf"{wss}"),
        ("some_whitespace",                 rf"{ws}+"),
        ("some_whitespaces",                rf"{wss}"),

        # --- Digits ---
        ("some_digit",                      rf"{digits}"),
        ("some_digits",                     rf"{digits}"),

        # --- Number ---
        ("some_number",         rf"{number}({wss}{number})*"),
        ("some_numbers",        rf"{number}({sep}{number})*"),
        ("some_mixed_number",   rf"{mixed_number}({sep}{mixed_number})*"),
        ("some_mixed_numbers",  rf"{mixed_number}({sep}{mixed_number})*"),

        # --- letters ---
        ("some_letter",                     rf"{letter}+"),
        ("some_letters",                    rf"{letters}"),

        # --- alphabet numeric ---
        ("some_alnum",                      rf"{alnum}+"),
        ("some_alnums",                     rf"{alnum}+"),

        # --- graph ---
        ("some_graph",                      rf"{graph}+"),
        ("some_graphs",                     rf"{graph}+"),

        # --- punctuations ---
        ("some_punct",                      rf"{punct}+"),
        ("some_puncts",                     rf"{puncts}"),

        # --- space or punctuation ---
        ("some_space_or_punct",             rf"{space_or_punct}+"),

        # --- letter or punctuation ---
        ("some_letter_or_punct",            rf"{letter_or_punct}+"),

        # --- word ---
        ("some_word",                       rf"{word}({sep}{word})*"),
        ("some_words",                      rf"{word}({sep}{word})*"),

        # --- mixed-word ---
        ("some_mixed_word",                 rf"{mixed_word}({sep}{mixed_word})*"),

        # --- non-whitespace(s) ---
        ("some_non_ws",                     rf"{non_wss}"),
        ("some_non_wss",                    rf"{non_wss}"),
    ]
)
def test_some_quantity_variant_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected
