"""
Unit tests for the `textfsmgen.gp.TranslatedMixedNumberPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_mixed_number_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_mixed_number_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
# TranslatedDigitPattern,
# TranslatedDigitsPattern,
# TranslatedNumberPattern,
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


class TestTranslatedMixedNumberPatternClass:
    """Test suite for TranslatedMixedNumberPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedMixedNumberPattern instance for reuse."""
        self.mixed_number_node = TranslatedMixedNumberPattern("-1.1")

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_number_node.is_subset_of(other_instance) is True

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_number_node.is_subset_of(other_instance) is False

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_number_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "-1.1",  # mixed-number
                # When mixed-number is combined with a mixed-number,
                # the recommendation should produce a mixed-number pattern.
                TranslatedMixedNumberPattern
            ),
            (
                "abc.123",  # mixed-word
                # When mixed-number is combined with a mixed-word,
                # the recommendation should produce a mixed-word pattern.
                TranslatedMixedWordPattern
            ),
            (
                "a.1 b.2",  # mixed-words
                # When mixed-number is combined with mixed-words,
                # the recommendation should produce mixed-words pattern.
                TranslatedMixedWordsPattern
            ),
            (
                "abc\xc8",  # non-whitespaces
                # When mixed-number is combined with non-whitespaces,
                # the recommendation should produce non-whitespaces pattern.
                TranslatedNonWhitespacesPattern
            ),
            (
                "abc\xc8 xyz",  # non-whitespace group
                # When mixed-number is combined with non-whitespaces,
                # the recommendation should produce non-whitespace group pattern.
                TranslatedNonWhitespacesGroupPattern
            ),
        ],
    )
    def test_recommend_method_case_subset(self, number, expected_class):
        """
        Verify that a mixed-number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_number_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            (
                "1",    # digit
                # When mixed-number are combined with a digit,
                # the recommendation should produce mixed-number pattern.
                TranslatedMixedNumberPattern
            ),
            (
                "12",  # digits
                # When mixed-number are combined with digits,
                # the recommendation should produce mixed-number pattern.
                TranslatedMixedNumberPattern
            ),
            (
                "1.2",  # number
                # When mixed-number are combined with number,
                # the recommendation should produce mixed-number pattern.
                TranslatedMixedNumberPattern
            ),
        ],
    )
    def test_recommend_method_case_superset(self, number, expected_class):
        """
        Verify that mixed-number type correctly recommends a subset type
        when combined with compatible number.
        """
        args = to_list(number)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_number_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "number, expected_class",
        [
            # When a mixed-number is combined with letters, alphanumeric characters,
            # graphs, or word,
            # the recommendation should produce a TranslatedMixedWordPattern.
            (
                "a",  # letter
                TranslatedMixedWordPattern
            ),
            (
                "ab",  # letters
                TranslatedMixedWordPattern
            ),
            (
                ["a", "1"], # an alphabet or numeric
                TranslatedMixedWordPattern
            ),
            (
                ["a", "1", "#"], # a graph character
                TranslatedMixedWordPattern
            ),
            (
                "abc123",   # a word
                TranslatedMixedWordPattern
            ),

            # ====================
            # When a mixed-number is combined with words,
            # the recommendation should produce a TranslatedMixedWordPattern.
            (
                    "a1 b2",  # words
                    TranslatedMixedWordsPattern
            ),

            # ====================
            # When a mixed-number is combined with punctuation(s) or non-whitespace(s)
            # the recommendation should produce a TranslatedNonWhitespacesPattern.
            (
                "+",  # a punctuation
                TranslatedNonWhitespacesPattern
            ),
            (
                "++--==",   # punctuations
                TranslatedNonWhitespacesPattern
            ),
            (
                "\xc8",  # a non-whitespace
                TranslatedNonWhitespacesPattern
            ),
            (
                "abc\xc8",  # multi-non-whitespace
                TranslatedNonWhitespacesPattern
            ),

            # ====================
            # When a number is combined with punctuation-group
            # the recommendation should produce a TranslatedNonWhitespacesGroupPattern.
            (
                    "++ -- ** ==",  # punctuation-group
                    TranslatedNonWhitespacesGroupPattern
            ),

        ],
    )
    def test_recommend_method_case_aggregating(self, number, expected_class):
        """
        Verify that mixed-type type correctly recommends a subset type
        when combined with compatible mixed-number.
        """
        args = to_list(number)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_number_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
