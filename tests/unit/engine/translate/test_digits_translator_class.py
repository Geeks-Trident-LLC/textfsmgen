"""
Unit tests for the `textfsmgen.engine.translate.DigitsTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_digits_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_digits_translator_class.py
"""

import pytest   # noqa

from textfsmgen.engine.translate import (
    make_translator,

    DigitsTranslator,
    NumberTranslator,
    MixedNumberTranslator,

    WordTranslator,
    WordsTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,

    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestDigitsTranslatorClass:
    """Test suite for DigitsTranslator class."""

    def setup_method(self):
        """Create a baseline DigitsTranslator instance for reuse."""
        self.translator = DigitsTranslator("12")

    @pytest.mark.parametrize(
        "other",
        [
            "123",              # digits are a subset of digits
            "1.1",              # digits are a subset of number
            "-1.1",             # digits are a subset of mixed number
            "abc123",           # digits are a subset of word
            "a1 b12",           # digits are a subset of words
            "abc.123",          # digits are a subset of mixed word
            "a.1 b.2",          # digits are a subset of mixed words
            "abc\xc8",          # digits are a subset of non-whitespaces
            "abc\xc8 xyz",      # digits are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that digits are a subset of (digits, number, mixed number,
        word(s), mixed word(s), non‑whitespaces, non-whitespace-group).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # digits are not a subset of digit
            "abc",              # digits are not a subset of letter(s)
            "-",                # digits are not a subset of punctuation
            "++--",             # digits are not a subset of punctuation(s)
            "++ -- ==",         # digits are not a subset of punctuation group
            "\xc8",             # digits are not a subset of non-whitespace
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that digits data is not a subset of (digit, letter(s),
        punctuation(s), punctuation-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # digit is a superset of digit
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that digits data is correctly identified as a superset of digit.
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "123",  # digits
                DigitsTranslator # (digits, digits) => digits
            ),
            (
                "1.1",  # number
                NumberTranslator # (digits, number) => number
            ),
            (
                "-1.1",  # mixed-number
                MixedNumberTranslator    # (digits, mixed-number) => mixed-number
            ),
            (
                "abc123",  # word
                WordTranslator   # (digits, word) => word
            ),
            (
                "a1 a12",  # words
                WordsTranslator  # (digits, words) => words
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator  # (digits, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (digits, mixed-words) => mixed-words
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (digits, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (digits, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that digits type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "1",  # digit
                DigitsTranslator # (digits, digit) => digits
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that digits type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "ab",  # letters
                WordTranslator   # (digits, letters) => word
            ),
            (
                "+",  # punctuation
                NonWSSTranslator # (digits, punct) => non-whitespaces
            ),
            (
                "++",  # punctuations
                NonWSSTranslator # (digits, puncts) => non-whitespaces
            ),
            (
                "++ -- ==",  # punctuation-group
                NonWSSGroupTranslator    # (digits, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that digits type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
