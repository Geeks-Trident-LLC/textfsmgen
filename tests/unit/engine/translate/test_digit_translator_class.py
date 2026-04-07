"""
Unit tests for the `textfsmgen.engine.translate.DigitTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_digit_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_digit_translator_class.py
"""

import pytest   # noqa

from textfsmgen.engine.translate import (
    PatternTranslator,
    DigitTranslator,
    DigitsTranslator,
    NumberTranslator,
    MixedNumberTranslator,

    AlnumTranslator,

    WordTranslator,
    WordsTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,
    NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestDigitTranslatorClass:
    """Test suite for DigitTranslator class."""

    def setup_method(self):
        """Create a baseline DigitTranslator instance for reuse."""
        self.translator = DigitTranslator("1", "2", "3")

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # digit is a subset of digit
            "123",              # digit is a subset of digits
            "1.1",              # digit is a subset of number
            "-1.1",             # digit is a subset of mixed number
            ["a", "1"],         # digit is a subset of alphabet numeric
            ["a", "1", "#"],    # digit is a subset of graph
            "abc123",           # digit is a subset of word
            "a1 b12",           # digit is a subset of words
            "abc.123",          # digit is a subset of mixed word
            "a.1 b.2",          # digit is a subset of mixed words
            "\xc8",             # digit is a subset of non-whitespace
            "abc\xc8",          # digit is a subset of non-whitespaces
            "abc\xc8 xyz",      # digit is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that a digit data is correctly identified as a subset of
        broader translated categories, including digits, numbers, graphs,
        words, and non‑whitespace.
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "abc",              # digit is not a subset of letter(s)
            "++--",             # digit is not a subset of punctuation(s)
            "++ -- ==",         # digit is not a subset of punctuation group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that a digit data is not a subset of letters or punctuations
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "123",              # digit is not a superset of digits
            "1.1",              # digit is not a superset of number
            "abc\xc8 xyz",      # digit is not a superset of non-whitespace group
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that a digit data is correctly identified as not belonging
        to any broader translated category.
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_superset_of(other_instance) is False

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "1",  # digit
                DigitTranslator  # (digit, digit) => digit
            ),
            (
                "123",  # digits
                DigitsTranslator # (digit, digits) => digits
            ),
            (
                "1.1",  # number
                NumberTranslator # (digit, number) => number
            ),
            (
                "-1.1",  # mixed-number
                MixedNumberTranslator    # (digit, mixed-number) => mixed-number
            ),
            (
                "abc123",  # word
                WordTranslator   # (digit, word) => word
            ),
            (
                "a1 a12",  # words
                WordsTranslator  # (digit, words) => words
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator  # (digit, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (digit, mixed-words) => mixed-words
            ),
            (
                "\xc8",  # non-whitespace
                NonWSTranslator  # (digit, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (digit, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (digit, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that a digit type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",  # letter
                AlnumTranslator    # (digit, letter) => alphabet-numeric
            ),
            (
                "ab",  # letters
                WordTranslator   # (digit, letters) => word
            ),
            (
                "+",  # punctuation
                NonWSTranslator  # (digit, punct) => non-whitespace
            ),
            (
                "++",  # punctuations
                NonWSSTranslator # (digit, puncts) => non-whitespaces
            ),
            (
                "++ -- ==",  # punctuation-group
                NonWSSGroupTranslator    # (digit, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that a digit type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)