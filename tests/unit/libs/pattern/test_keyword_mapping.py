"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_keyword_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_keyword_mapping.py
"""

import pytest   # noqa

from textfsmgen.libs.pattern import ParsedKeywordMappingName

class PAT:

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


@pytest.mark.parametrize(
    "name, expected",
    [
        # --- Generic wildcard ---
        ("dot",                         rf"{PAT.dot}"),
        ("dots",                        rf"{PAT.dot}+"),
        ("anything",                    rf"{PAT.dot}*"),
        ("something",                   rf"{PAT.dot}+"),

        # --- Literal spaces ---
        ("space",                       rf"{PAT.space}"),
        ("spaces",                      rf"{PAT.space}+"),

        # --- Whitespace ---
        ("ws",                          rf"{PAT.ws}"),
        ("wss",                         rf"{PAT.wss}"),
        ("whitespace",                  rf"{PAT.ws}"),
        ("whitespaces",                 rf"{PAT.ws}+"),

        # --- Digits ---
        ("digit",                       rf"{PAT.digit}"),
        ("digits",                      rf"{PAT.digit}+"),

        # --- Number ---
        ("number",                      rf"{PAT.number}"),
        ("mixed_number",                rf"{PAT.mixed_number}"),

        # --- letters ---
        ("letter",                      rf"{PAT.letter}"),
        ("letters",                     rf"{PAT.letters}"),
        ("optional_letters_group",      rf"{PAT.letters}({PAT.wss}{PAT.letters})*"),
        ("letters_group",               rf"{PAT.letters}({PAT.wss}{PAT.letters})+"),

        # --- alphabet numeric ---
        ("alnum",                       rf"{PAT.alnum}"),

        # --- graph ---
        ("graph",                       rf"{PAT.graph}"),

        # --- punctuations ---
        ("punct",                       rf"{PAT.punct}"),
        ("puncts",                      rf"{PAT.punct}+"),
        ("puncts_group",                rf"{PAT.puncts}({PAT.wss}{PAT.puncts})+"),

        # --- space or punctuation ---
        ("space_or_punct",              rf"{PAT.space_or_punct}"),

        # --- letter or punctuation ---
        ("letter_or_punct",             rf"{PAT.letter_or_punct}"),

        # --- word ---
        ("word",                        rf"{PAT.word}"),
        ("words",                       rf"{PAT.word}({PAT.wss}{PAT.word})*"),
        ("optional_word_group",         rf"{PAT.word}({PAT.wss}{PAT.word})*"),
        ("word_group",                  rf"{PAT.word}(\s+{PAT.word})+"),

        # --- mixed-word ---
        ("mixed_word",                  rf"{PAT.mixed_word}"),
        ("mixed_words",                 rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})*"),
        ("optional_mixed_word_group",   rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})*"),
        ("mixed_word_group",            rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})+"),

        # --- non-whitespace(s) ---
        ("non_ws",                      rf"{PAT.non_ws}"),
        ("non_wss",                     rf"{PAT.non_ws}+"),
        ("optional_non_wss_group",      rf"{PAT.non_wss}({PAT.wss}{PAT.non_wss})*"),
        ("non_wss_group",               rf"{PAT.non_wss}({PAT.wss}{PAT.non_wss})+"),
    ]
)
def test_core_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name",
    [
        "numbers",
        "mixed_numbers",
        "graphs",
        "alnums",
    ]
)
def test_incompatible_keyword(name):
    parser = ParsedKeywordMappingName("numbers")
    assert not parser.keyword


@pytest.mark.parametrize(
    "name, expected",
    [
        # --- Generic wildcard ---
        ("some_dot",                        rf"{PAT.dot}+"),
        ("some_dots",                       rf"{PAT.dot}+"),

        # --- Literal spaces ---
        ("some_space",                      rf"{PAT.space}+"),
        ("some_spaces",                     rf"{PAT.space}+"),

        # --- Whitespace ---
        ("some_ws",                         rf"{PAT.ws}+"),
        ("some_wss",                        rf"{PAT.wss}"),
        ("some_whitespace",                 rf"{PAT.ws}+"),
        ("some_whitespaces",                rf"{PAT.wss}"),

        # --- Digits ---
        ("some_digit",                      rf"{PAT.digit}+"),
        ("some_digits",                     rf"{PAT.digits}"),

        # --- Number ---
        # ("some_number",                     rf"{PAT.number}"),
        # ("some_mixed_number",               rf"{PAT.mixed_number}"),

        # --- letters ---
        ("some_letter",                     rf"{PAT.letter}+"),
        ("some_letters",                    rf"{PAT.letters}"),
        # ("some_optional_letters_group",     rf"{PAT.letters}({PAT.wss}{PAT.letters})*"),
        # ("some_letters_group",              rf"{PAT.letters}({PAT.wss}{PAT.letters})+"),

        # --- alphabet numeric ---
        ("some_alnum",                      rf"{PAT.alnum}+"),

        # --- graph ---
        ("some_graph",                      rf"{PAT.graph}+"),

        # --- punctuations ---
        ("some_punct",                      rf"{PAT.punct}+"),
        ("some_puncts",                     rf"{PAT.puncts}"),
        # ("some_puncts_group",               rf"{PAT.puncts}({PAT.wss}{PAT.puncts})+"),

        # --- space or punctuation ---
        ("some_space_or_punct",             rf"{PAT.space_or_punct}+"),

        # --- letter or punctuation ---
        ("some_letter_or_punct",            rf"{PAT.letter_or_punct}+"),

        # --- word ---
        ("some_word",                       rf"{PAT.word}"),     # need to check its logic
        ("some_words",                      rf"{PAT.word}({PAT.wss}{PAT.word})*"),
        # ("some_optional_word_group",        rf"{PAT.word}({PAT.wss}{PAT.word})*"),
        # ("some_word_group",                 rf"{PAT.word}(\s+{PAT.word})+"),

        # --- mixed-word ---
        ("some_mixed_word",                 rf"{PAT.mixed_word}"),   # need to check its logic
        # ("some_mixed_words",                rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})*"),
        ("some_optional_mixed_word_group",  rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})*"),
        # ("some_mixed_word_group",           rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})+"),

        # --- non-whitespace(s) ---
        ("some_non_ws",                     rf"{PAT.non_ws}+"),
        ("some_non_wss",                    rf"{PAT.non_wss}"),
        ("some_optional_non_wss_group",     rf"{PAT.non_wss}({PAT.wss}{PAT.non_wss})*"),
        # ("some_non_wss_group",              rf"{PAT.non_wss}({PAT.wss}{PAT.non_wss})+"),
    ]
)
def test_some_quantity_variant_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # --- Generic wildcard ---
        ("optional_dot",                rf"{PAT.dot}?"),
        ("optional_dots",               rf"{PAT.dot}*"),

        # --- Literal spaces ---
        ("optional_space",              rf"{PAT.space}?"),
        ("optional_spaces",             rf"{PAT.space}*"),

        # --- Whitespace ---
        ("optional_ws",                 rf"{PAT.ws}?"),
        ("optional_wss",                rf"{PAT.ws}*"),
        ("optional_whitespace",         rf"{PAT.ws}?"),
        ("optional_whitespaces",        rf"{PAT.ws}*"),

        # --- Digits ---
        ("optional_digit",              rf"{PAT.digit}?"),
        ("optional_digits",             rf"{PAT.digit}*"),

        # --- Number ---
        ("optional_number",             rf"({PAT.number})?"),
        ("optional_mixed_number",       rf"({PAT.mixed_number})?"),

        # --- letters ---
        ("optional_letter",             rf"{PAT.letter}?"),
        ("optional_letters",            rf"{PAT.letter}*"),
        ("optional_letters_group",      rf"{PAT.letters}({PAT.wss}{PAT.letters})*"),

        # --- alphabet numeric ---
        ("optional_alnum",              rf"{PAT.alnum}?"),

        # --- graph ---
        ("optional_graph",              rf"{PAT.graph}?"),

        # --- punctuations ---
        ("optional_punct",              rf"{PAT.punct}?"),
        ("optional_puncts",             rf"{PAT.punct}*"),
        ("optional_puncts_group",       rf"{PAT.puncts}({PAT.wss}{PAT.puncts})*"),

        # --- space or punctuation ---
        ("optional_space_or_punct",     rf"{PAT.space_or_punct}?"),

        # --- letter or punctuation ---
        ("optional_letter_or_punct",    rf"{PAT.letter_or_punct}?"),

        # --- word ---
        ("optional_word",               rf"({PAT.word})?"),
        ("optional_words",              rf"({PAT.word}({PAT.wss}{PAT.word})*)?"),
        ("optional_word_group",         rf"{PAT.word}({PAT.wss}{PAT.word})*"),

        # --- mixed-word ---
        ("optional_mixed_word",         rf"({PAT.mixed_word})?"),
        # ("optional_mixed_words",        rf"({PAT.mixed_word}({PAT.wss}{PAT.mixed_word})*)?"),
        ("optional_mixed_word_group",   rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word})*"),

        # --- non-whitespace(s) ---
        ("optional_non_ws",             rf"{PAT.non_ws}?"),
        ("optional_non_wss",            rf"{PAT.non_ws}*"),
        ("optional_non_wss_group",      rf"{PAT.non_wss}({PAT.wss}{PAT.non_wss})*"),
    ]
)
def test_optional_quantity_variant_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # --- Generic wildcard ---
        ("3_dot",               rf"{PAT.dot}{{3}}"),
        ("three_dot",           rf"{PAT.dot}{{3}}"),
        ("3dot",                rf"{PAT.dot}{{3}}"),
        ("fortyfive_dot",       rf"{PAT.dot}{{45}}"),

        # --- Literal spaces ---
        ("3_space",             rf"{PAT.space}{{3}}"),
        ("3_spaces",            rf"{PAT.spaces}({PAT.wss}{PAT.spaces}){{2}}"),

        # --- Whitespace ---
        ("three_ws",            rf"{PAT.ws}{{3}}"),
        ("3_whitespace",        rf"{PAT.ws}{{3}}"),
        # ("3_wss",               rf"{PAT.wss}({PAT.wss}{PAT.wss}){{2}}"),


        # --- Digits ---
        ("3_digit",             rf"{PAT.digit}{{3}}"),
        ("3digit",              rf"{PAT.digit}{{3}}"),
        ("3_digits",            rf"{PAT.digits}({PAT.wss}{PAT.digits}){{2}}"),


        # --- Number ---
        ("3_number",            rf"{PAT.number}({PAT.wss}{PAT.number}){{2}}"),
        ("3_mixed_number",      rf"{PAT.mixed_number}({PAT.wss}{PAT.mixed_number}){{2}}"),

        # --- letters ---
        ("3_letter",            rf"{PAT.letter}{{3}}"),
        ("3_letters",           rf"{PAT.letters}({PAT.wss}{PAT.letters}){{2}}"),

        # --- alphabet numeric ---
        ("3_alnum",             rf"{PAT.alnum}{{3}}"),

        # --- graph ---
        ("3_graph",             rf"{PAT.graph}{{3}}"),

        # --- punctuations ---
        ("3_punct",             rf"{PAT.punct}{{3}}"),
        ("3_puncts",            rf"{PAT.punct}+({PAT.wss}{PAT.puncts}){{2}}"),

        # --- space or punctuation ---
        ("3_space_or_punct",    rf"{PAT.space_or_punct}{{3}}"),

        # --- letter or punctuation ---
        ("3_letter_or_punct",   rf"{PAT.letter_or_punct}{{3}}"),

        # --- word ---
        ("3_word",              rf"{PAT.word}({PAT.wss}{PAT.word}){{2}}"),
        # ("3_words",             rf"{PAT.word}({PAT.wss}{PAT.word}){{2}}"),

        # --- mixed-word ---
        ("3_mixed_word",        rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word}){{2}}"),
        # ("3_mixed_words",       rf"{PAT.mixed_word}({PAT.wss}{PAT.mixed_word}){{2}}"),

        # --- non-whitespace(s) ---
        ("3_non_ws",            rf"{PAT.non_ws}{{3}}"),
        ("3_non_wss",           rf"{PAT.non_wss}({PAT.wss}{PAT.non_wss}){{2}}"),
    ]
)
def test_exact_quantity_variant_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # test singular char
        ("1_3_letter",           rf"{PAT.letter}{{1,3}}"),
        ("one_3_letter",         rf"{PAT.letter}{{1,3}}"),
        ("one_three_letter",     rf"{PAT.letter}{{1,3}}"),
        ("one_to_three_letter",  rf"{PAT.letter}{{1,3}}"),
        ("one_to_3_letter",      rf"{PAT.letter}{{1,3}}"),
        ("1_to_3_letter",        rf"{PAT.letter}{{1,3}}"),

        ("_3_letter",            rf"{PAT.letter}{{,3}}"),
        ("_three_letter",        rf"{PAT.letter}{{,3}}"),
        ("_to_three_letter",     rf"{PAT.letter}{{,3}}"),
        ("_to_3_letter",         rf"{PAT.letter}{{,3}}"),

        ("2__letter",           rf"{PAT.letter}{{2,}}"),
        ("two__letter",         rf"{PAT.letter}{{2,}}"),
        ("two_to__letter",      rf"{PAT.letter}{{2,}}"),

        ("0_3_letter",           rf"{PAT.letter}{{,3}}"),
    ]
)
def test_range_quantity_variant_single_char_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # test multiple chars
        ("1_3_letters",             rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("one_3_letters",           rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("one_three_letters",       rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("one_to_three_letters",    rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("one_to_3_letters",        rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("1_to_3_letters",          rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),

        ("_3_letters",              rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("_three_letters",          rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("_to_three_letters",       rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("_to_3_letters",           rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),

        ("2__letters",              rf"{PAT.letters}({PAT.wss}{PAT.letters}){{1,}}"),
        ("two__letters",            rf"{PAT.letters}({PAT.wss}{PAT.letters}){{1,}}"),
        ("two_to__letters",         rf"{PAT.letters}({PAT.wss}{PAT.letters}){{1,}}"),

        ("1__letters",              rf"{PAT.letters}({PAT.wss}{PAT.letters})*"),
        ("one__letters",            rf"{PAT.letters}({PAT.wss}{PAT.letters})*"),
        ("one_to__letters",         rf"{PAT.letters}({PAT.wss}{PAT.letters})*"),

        ("0_3_letters",             rf"{PAT.letters}({PAT.wss}{PAT.letters}){{,2}}"),
        ("2_5_letters",             rf"{PAT.letters}({PAT.wss}{PAT.letters}){{1,4}}"),
    ]
)
def test_range_quantity_variant_multiple_chars_keyword(name, expected):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.pattern == expected