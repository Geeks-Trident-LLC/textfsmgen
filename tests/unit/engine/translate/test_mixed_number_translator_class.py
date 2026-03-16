"""
Unit tests for the `textfsmgen.engine.translate.MixedNumberTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/translate/test_mixed_number_translator_class.py
    or
    $ python -m pytest tests/unit/engine/translate/test_mixed_number_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    PatternTranslator,
# DigitTranslator,
# DigitsTranslator,
# NumberTranslator,
    MixedNumberTranslator,
# LetterTranslator,
# LettersTranslator,
# AlnumTranslator,
# PunctTranslator,
# PunctsTranslator,
# PunctsGroupTranslator,
# GraphTranslator,
# WordTranslator,
# WordsTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,
# NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestMixedNumberTranslatorClass:
    """Test suite for MixedNumberTranslator class."""

    def setup_method(self):
        """Create a baseline MixedNumberTranslator instance for reuse."""
        self.translator = MixedNumberTranslator("-1.1")

    @pytest.mark.parametrize(
        "other",
        [
            "-1.1",             # mixed-number is a subset of a mixed-number
            "abc.123",          # mixed-number is a subset of a mixed-word
            "a.1 b.1",          # mixed-number is a subset of mixed-words
            "abc\xc8",          # mixed-number is a subset of non-whitespaces
            "abc\xc8 xyz",      # mixed-number is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that a mixed number is a subset of (mixed number,
        mixed-word(s), non-whitespaces, non-whitespace-group)
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # mixed-number is not a subset of digit
            "123",              # mixed-number is not a subset of digits
            "1.23",             # mixed-number is not a subset of number
            "a",                # mixed-number is not a subset of letter
            "abc",              # mixed-number is not a subset of letter(s)
            "+",                # mixed-number is not a subset of punctuation
            "++--",             # mixed-number is not a subset of punctuation(s)
            "++ -- ==",         # mixed-number is not a subset of punctuation group
            "\xc8",             # mixed-number is not a subset of non-whitespace
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that number is not a subset of (digit, digits, letter(s),
        punctuation(s), punctuation group, non-whitespace)
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # mixed-number is a superset of digit
            "123",              # mixed-number is a superset of digits
            "1.2",              # mixed-number is a superset of number
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that number is a superset of (digit, digits, number).
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "-1.1",  # mixed-number
                MixedNumberTranslator    # (mixed-number, mixed-number) => mixed-number
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator  # (mixed-number, mixed-word) => mixed-word
            ),
            (
                "a.1 b.2",  # mixed-words
                MixedWordsTranslator # (mixed-number, mixed-words) => mixed-words
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (mixed-number, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator # (mixed-number, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, number, expected_class):
        """
        Verify that a mixed-number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "1",  # digit
                MixedNumberTranslator    # (mixed-number, digit) => mixed-number
            ),
            (
                "12",  # digits
                MixedNumberTranslator    # (mixed-number, digits) => mixed-number
            ),
            (
                "1.2",  # number
                MixedNumberTranslator    # (mixed-number, number) => mixed-number
            ),
        ],
    )
    def test_recommend_method_case_superset(self, number, expected_class):
        """
        Verify that mixed-number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "a",  # letter
                MixedWordTranslator  # (mixed-number, letter) => mixed-word
            ),
            (
                "ab",  # letters
                MixedWordTranslator  # (mixed-number, letters) => mixed-word
            ),
            (
                    ["a", "1"],  # alphabet-numeric
                    MixedWordTranslator  # (mixed-number, alphabet-numeric) => mixed-word
            ),
            (
                    ["a", "1", "#"],  # graph
                    MixedWordTranslator  # (mixed-number, graph) => mixed-word
            ),
            (
                "abc123",  # word
                MixedWordTranslator  # (mixed-number, word) => mixed-word
            ),
            (
                "a1 b2",  # words
                MixedWordsTranslator # (mixed-number, words) => mixed-words
            ),
            (
                "+",  # punctuation
                NonWSSTranslator # (mixed-number, punct) => non-whitespaces
            ),
            (
                "++--==",  # punctuations
                NonWSSTranslator # (mixed-number, puncts) => non-whitespaces
            ),
            (
                "\xc8",  # non-whitespace
                NonWSSTranslator # (mixed-number, non-whitespace) => non-whitespaces
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (mixed-number, non-whitespaces) => non-whitespaces
            ),
            (
                    "++ -- ** ==",  # punctuation-group
                    NonWSSGroupTranslator # (mixed-number, punct-group) => non-whitespace-group
            ),

        ],
    )
    def test_recommend_method_case_aggregating(self, number, expected_class):
        """
        Verify that mixed-number type correctly recommends a subset type
        when combined with compatible mixed-number.
        """
        args = to_list(number)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
