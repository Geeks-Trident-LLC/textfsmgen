"""
Unit tests for the `textfsmgen.libs.pattern.ParsedKeywordMappingName` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern/test_parsed_base_keyword_mapping.py
    or
    $ python -m pytest tests/unit/libs/pattern/test_parsed_base_keyword_mapping.py
"""

import pytest

from textfsmgen.libs.pattern import ParsedKeywordMappingName

@pytest.mark.parametrize(
    "name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi",
    [
        ("word","word", None, None, None),

        # variants
        ("optional_word",           "word",     "optional",         None, None),
        ("optional_word_group",     "word",     "optional_group",   None, None),
        ("some_word", "word",       "some",     None,               None),
        ("zero_or_one_word",        "word",     "zero_or_one",      None, None),
        ("zero_or_more_word",       "word",     "zero_or_more",     None, None),
        ("one_or_more_word",        "word",     "one_or_more",      None, None),
    ]
)
def test_variants(name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.base_keyword == exp_base
    assert parser.quantity == exp_qty
    assert parser.quantity_lo == exp_qty_lo
    assert parser.quantity_hi == exp_qty_hi

@pytest.mark.parametrize(
    "name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi",
    [
        # exact-quantity
        ("three_word",      "word",     "3",    None, None),
        ("3_word",          "word",     "3",    None, None),
        ("3word",           "word",     "3",    None, None),

    ]
)
def test_exact_quantity(name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.base_keyword == exp_base
    assert parser.quantity == exp_qty
    assert parser.quantity_lo == exp_qty_lo
    assert parser.quantity_hi == exp_qty_hi


@pytest.mark.parametrize(
    "name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi",
    [
        # range-quantity
        ("1_to_5_word",         "word",     None,   "1",    "5"),
        ("0_to_5_word",         "word",     None,   "",     "5"),
        ("_to_5_word",          "word",     None,   "",     "5"),

        ("one_to_five_word",    "word",     None,   "1",    "5"),
        ("zero_to_five_word",   "word",     None,   "",     "5"),
        ("_to_five_word",       "word",     None,   "",     "5"),

        ("1_to__word",          "word",     None,   "1",    ""),
        ("0_to__word",          "word",     None,   "",     ""),
        ("_to_n_word",          "word",     None,   "",     ""),
        ("zero_to_n_word",      "word",     None,   "",     ""),

    ]
)
def test_semantic_range_quantity(name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.base_keyword == exp_base
    assert parser.quantity == exp_qty
    assert parser.quantity_lo == exp_qty_lo
    assert parser.quantity_hi == exp_qty_hi


@pytest.mark.parametrize(
    "name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi",
    [
        # range-quantity
        ("1_to_5_words",        "word",    None,   "1",    "5"),
        ("0_to_5_words",        "word",    None,   "",     "5"),
        ("_to_5_words",         "word",    None,   "",     "5"),

        ("one_to_five_words",   "word",    None,   "1",    "5"),
        ("zero_to_five_words",  "word",    None,   "",     "5"),
        ("_to_five_words",      "word",    None,   "",     "5"),

        ("1_to__words",         "word",     None,   "1",    ""),
        ("0_to__words",         "word",     None,   "",     ""),
        ("_to_n_words",         "word",     None,   "",     ""),
        ("zero_to_n_words",     "word",     None,   "",     ""),

    ]
)
def test_plural_semantic_range_quantity(name, exp_base, exp_qty, exp_qty_lo, exp_qty_hi):
    parser = ParsedKeywordMappingName(name)
    assert parser.keyword == name
    assert parser.base_keyword == exp_base
    assert parser.quantity == exp_qty
    assert parser.quantity_lo == exp_qty_lo
    assert parser.quantity_hi == exp_qty_hi