"""
Unit tests for runtime exception handling in the `textfsmgen.gp` module.

This test module validates that unimplemented recommendation cases
within translated pattern classes correctly raise a dynamically
generated runtime exception (`NotImplementRecommendedRTPattern`).

Coverage
--------
- Ensures `is_subset_of`, `is_superset_of`, and `recommend` methods
  raise the expected exception when interacting with unsupported
  or dummy patterns.
- Confirms that exception names and messages are consistent with
  the runtime error generation logic.

Usage
-----
Run pytest in the project root to execute these tests:

    $ pytest tests/unit/gp/test_gp_raise_runtime_exception.py
    or
    $ python -m pytest tests/unit/gp/test_gp_raise_runtime_exception.ply
"""

import pytest

from textfsmgen.engine.translate import PatternTranslator

from tests.unit.gp import TranslatedDummyPattern


to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


@pytest.mark.parametrize(
    "data",
    [
        "1",            # a digit
        "123",          # digits
        "1.1",          # a number
        "-1.1",         # a mixed number
        "a",            # a letter
        "abc",          # letters
        ["a", "1"],     # alphabet or numeric
        "-",            # a punctuation
        "+-*:",         # punctuations
        "-- ++ ==",     # punctuation group
        ["a", "1", "#"],    # a graph
        "abc123",       # a word
        "a1 b12",       # words
        "abc.123",      # a mixed word
        "a.1 b.2",      # a mixed words
        "\xc8",         # non-whitespace
        "abc\xc8",      # multiple non-whitespace
        "abc\xc8 xyz",  # non-whitespace group
    ]
)
def test_raise_exception_in_is_subset_of(data):
    """
    Verify that `is_subset_of` raises a NotImplementRecommendedRTPattern
    when called with an unsupported dummy pattern.
    """
    dummy_other = TranslatedDummyPattern()
    args = to_list(data)
    translated_pattern_node = PatternTranslator.do_factory_create(*args)
    with pytest.raises(Exception) as ex:
        translated_pattern_node.is_subset_of(dummy_other)
    assert ex.type.__name__ == "NotImplementRecommendedRTPattern"


@pytest.mark.parametrize(
    "data",
    [
        "1",            # a digit
        "123",          # digits
        "1.1",          # a number
        "-1.1",         # a mixed number
        "a",            # a letter
        "abc",          # letters
        ["a", "1"],     # alphabet or numeric
        "-",            # a punctuation
        "+-*:",         # punctuations
        "-- ++ ==",     # punctuation group
        ["a", "1", "#"],    # a graph
        "abc123",       # a word
        "a1 b12",       # words
        "abc.123",      # a mixed word
        "a.1 b.2",      # a mixed words
        "\xc8",         # non-whitespace
        "abc\xc8",      # multiple non-whitespace
        "abc\xc8 xyz",  # non-whitespace group
    ]
)
def test_raise_exception_in_is_superset_of(data):
    """
    Verify that `is_superset_of` raises a NotImplementRecommendedRTPattern
    when called with an unsupported dummy pattern.
    """
    dummy_other = TranslatedDummyPattern()
    args = to_list(data)
    translated_pattern_node = PatternTranslator.do_factory_create(*args)
    with pytest.raises(Exception) as ex:
        translated_pattern_node.is_subset_of(dummy_other)
    assert ex.type.__name__ == "NotImplementRecommendedRTPattern"

@pytest.mark.parametrize(
    "data",
    [
        "1",            # a digit
        "123",          # digits
        "1.1",          # a number
        "-1.1",         # a mixed number
        "a",            # a letter
        "abc",          # letters
        ["a", "1"],     # alphabet or numeric
        "-",            # a punctuation
        "+-*:",         # punctuations
        "-- ++ ==",     # punctuation group
        ["a", "1", "#"],    # a graph
        "abc123",       # a word
        "a1 b12",       # words
        "abc.123",      # a mixed word
        "a.1 b.2",      # a mixed words
        "\xc8",         # non-whitespace
        "abc\xc8",      # multiple non-whitespace
        "abc\xc8 xyz",  # non-whitespace group
    ]
)
def test_raise_exception_in_is_superset_of(data):
    """
    Verify that `recommend` raises a NotImplementRecommendedRTPattern
    when called with an unsupported dummy pattern.
    """
    dummy_other = TranslatedDummyPattern()
    args = to_list(data)
    translated_pattern_node = PatternTranslator.do_factory_create(*args)
    with pytest.raises(Exception) as ex:
        translated_pattern_node.is_subset_of(dummy_other)
    assert ex.type.__name__ == "NotImplementRecommendedRTPattern"
