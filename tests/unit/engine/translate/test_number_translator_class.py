"""
Unit tests for the `textfsmgen.engine.translate.NumberTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_number_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_number_translator_class.py
"""

import pytest   # noqa

from textfsmgen.engine.translate import (
    make_translator,

    NumberTranslator,
    MixedNumberTranslator,

    MixedWordTranslator,
    MixedWordsTranslator,

    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestNumberTranslatorClass:
    """Test suite for NumberTranslator class."""

    def setup_method(self):
        """Create a baseline NumberTranslator instance for reuse."""
        self.translator = NumberTranslator("1.1")

    @pytest.mark.parametrize(
        "other",
        [
            "1.1",              # number is a subset of number
            "-1.1",             # number is a subset of mixed number
            "abc\xc8",          # number is a subset of non-whitespaces
            "abc\xc8 xyz",      # number is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that number is a subset of (number, mixed number,
        non-whitespaces, non-whitespace-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # number is not a subset of digit
            "123",              # number is not a subset of digits
            "a",                # number is not a subset of letter
            "abc",              # number is not a subset of letter(s)
            "+",                # number is not a subset of punctuation
            "++--",             # number is not a subset of punctuation(s)
            "++ -- ==",         # number is not a subset of punctuation group
            "\xc8",             # number is not a subset of non-whitespace
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that number is not a subset of (digit, digits, letter(s),
        punctuation(s), punctuation group, non-whitespace)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # number is a superset of digit
            "123",              # number is a superset of digits
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that number is a superset of (digit, digits).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "1.1",  # number
                NumberTranslator # (number, number) => number
            ),
            (
                "-1.1",  # mixed-number
                MixedNumberTranslator    # (number, mixed-number) => mixed-number
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (number, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator # (number, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, number, expected_class):
        """
        Verify that a number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "1",  # digit
                NumberTranslator # (number, digit) => number
            ),
            (
                "12",  # digits
                NumberTranslator # (number, digits) => number
            ),
        ],
    )
    def test_recommend_method_case_superset(self, number, expected_class):
        """
        Verify that number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "a",  # letter
                MixedWordTranslator  # (number, letter) => mixed-word
            ),
            (
                "ab",  # letters
                MixedWordTranslator  # (number, letters) => mixed-word
            ),
            (
                    ["a", "1"],  # alphabet-numeric
                    MixedWordTranslator  # (number, alphabet-numeric) => mixed-word
            ),
            (
                    ["a", "1", "#"],  # graph
                    MixedWordTranslator  # (number, graph) => mixed-word
            ),
            (
                "abc123",  # word
                MixedWordTranslator  # (number, word) => mixed-word
            ),
            (
                    "a1 b1",  # words
                    MixedWordsTranslator # (number, words) => mixed-words
            ),
            (
                "+",  # punctuation
                NonWSSTranslator # (number, punct) => non-whitespaces
            ),
            (
                "++--==",  # punctuations
                NonWSSTranslator # (number, puncts) => non-whitespaces
            ),
            (
                "\xc8",  # non-whitespace
                NonWSSTranslator # (number, non-whitespace) => non-whitespaces
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (number, non-whitespaces) => non-whitespaces
            ),
            (
                    "++ -- ** ==",  # punctuation-group
                    NonWSSGroupTranslator # (number, non-whitespace-group) => non-whitespace-group
            ),

        ],
    )
    def test_recommend_method_case_aggregating(self, number, expected_class):
        """
        Verify that number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
