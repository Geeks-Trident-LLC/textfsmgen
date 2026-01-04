"""
Unit tests for the `textfsmgen.gp.TranslatedDigitPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_digit_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_digit_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
TranslatedDigitPattern,
TranslatedDigitsPattern,
TranslatedNumberPattern,
TranslatedMixedNumberPattern,
# TranslatedLetterPattern,
# TranslatedLettersPattern,
TranslatedAlphabetNumericPattern,
# TranslatedPunctPattern,
# TranslatedPunctsPattern,
# TranslatedPunctsGroupPattern,
# TranslatedGraphPattern,
TranslatedWordPattern,
TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedDigitPatternClass:
    """Test suite for TranslatedDigitPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedDigitPattern instance for reuse."""
        self.digit_node = TranslatedDigitPattern("1", "2", "3")

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.digit_node.is_subset_of(other_instance) is True

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.digit_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # digit is not a superset of digit
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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.digit_node.is_superset_of(other_instance) is False

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "1",                    # digit
                TranslatedDigitPattern  # (digit, digit) => digit
            ),
            (
                "123",                  # digits
                TranslatedDigitsPattern # (digit, digits) => digits
            ),
            (
                "1.1",                  # number
                TranslatedNumberPattern # (digit, number) => number
            ),
            (
                "-1.1",                         # mixed-number
                TranslatedMixedNumberPattern    # (digit, mixed-number) => mixed-number
            ),
            (
                "abc123",               # word
                TranslatedWordPattern   # (digit, word) => word
            ),
            (
                "a1 a12",               # words
                TranslatedWordsPattern  # (digit, words) => words
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (digit, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (digit, mixed-words) => mixed-words
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacePattern  # (digit, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (digit, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (digit, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that a digit type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.digit_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                                # letter
                TranslatedAlphabetNumericPattern    # (digit, letter) => alphabet-numeric
            ),
            (
                "ab",                   # letters
                TranslatedWordPattern   # (digit, letters) => word
            ),
            (
                "+",                            # punctuation
                TranslatedNonWhitespacePattern  # (digit, punct) => non-whitespace
            ),
            (
                "++",                           # punctuations
                TranslatedNonWhitespacesPattern # (digit, puncts) => non-whitespaces
            ),
            (
                "++ -- ==",                             # punctuation-group
                TranslatedNonWhitespacesGroupPattern    # (digit, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that a digit type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.digit_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)