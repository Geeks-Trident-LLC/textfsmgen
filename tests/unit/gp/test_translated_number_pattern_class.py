"""
Unit tests for the `textfsmgen.gp.TranslatedNumberPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_number_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_number_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
# TranslatedDigitPattern,
# TranslatedDigitsPattern,
TranslatedNumberPattern,
TranslatedMixedNumberPattern,
# TranslatedLetterPattern,
# TranslatedLettersPattern,
# TranslatedAlphabetNumericPattern,
# TranslatedPunctPattern,
# TranslatedPunctsPattern,
# TranslatedPunctsGroupPattern,
# TranslatedGraphPattern,
# TranslatedWordPattern,
# TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
# TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedNumberPatternClass:
    """Test suite for TranslatedNumberPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedNumberPattern instance for reuse."""
        self.number_node = TranslatedNumberPattern("1.1")

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.number_node.is_subset_of(other_instance) is True

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.number_node.is_subset_of(other_instance) is False

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.number_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "1.1",                  # number
                TranslatedNumberPattern # (number, number) => number
            ),
            (
                "-1.1",                         # mixed-number
                TranslatedMixedNumberPattern    # (number, mixed-number) => mixed-number
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (number, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                       # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern # (number, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, number, expected_class):
        """
        Verify that a number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.number_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "1",                    # digit
                TranslatedNumberPattern # (number, digit) => number
            ),
            (
                "12",                   # digits
                TranslatedNumberPattern # (number, digits) => number
            ),
        ],
    )
    def test_recommend_method_case_superset(self, number, expected_class):
        """
        Verify that number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.number_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "a",                        # letter
                TranslatedMixedWordPattern  # (number, letter) => mixed-word
            ),
            (
                "ab",                       # letters
                TranslatedMixedWordPattern  # (number, letters) => mixed-word
            ),
            (
                ["a", "1"],                 # alphabet-numeric
                TranslatedMixedWordPattern  # (number, alphabet-numeric) => mixed-word
            ),
            (
                ["a", "1", "#"],            # graph
                TranslatedMixedWordPattern  # (number, graph) => mixed-word
            ),
            (
                "abc123",                   # word
                TranslatedMixedWordPattern  # (number, word) => mixed-word
            ),
            (
                    "a1 b1",                    # words
                    TranslatedMixedWordsPattern # (number, words) => mixed-words
            ),
            (
                "+",                            # punctuation
                TranslatedNonWhitespacesPattern # (number, punct) => non-whitespaces
            ),
            (
                "++--==",                       # punctuations
                TranslatedNonWhitespacesPattern # (number, puncts) => non-whitespaces
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacesPattern # (number, non-whitespace) => non-whitespaces
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (number, non-whitespaces) => non-whitespaces
            ),
            (
                    "++ -- ** ==",                       # punctuation-group
                    TranslatedNonWhitespacesGroupPattern # (number, non-whitespace-group) => non-whitespace-group
            ),

        ],
    )
    def test_recommend_method_case_aggregating(self, number, expected_class):
        """
        Verify that number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.number_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
