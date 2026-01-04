"""
Unit tests for the `textfsmgen.gp.TranslatedDigitsPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_digits_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_digits_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
# TranslatedDigitPattern,
TranslatedDigitsPattern,
TranslatedNumberPattern,
TranslatedMixedNumberPattern,
# TranslatedLetterPattern,
# TranslatedLettersPattern,
# TranslatedAlphabetNumericPattern,
# TranslatedPunctPattern,
# TranslatedPunctsPattern,
# TranslatedPunctsGroupPattern,
# TranslatedGraphPattern,
TranslatedWordPattern,
TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
# TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

from tests.unit.gp import TranslatedDummyPattern

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedDigitsPatternClass:
    """Test suite for TranslatedDigitsPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedDigitsPattern instance for reuse."""
        self.digits_node = TranslatedDigitsPattern("12")

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.digits_node.is_subset_of(other_instance) is True

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
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.digits_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # digits is a superset of digit
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that a digits data is correctly identified as a superset of digit.
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.digits_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "123",  # digits
                # When a digit is combined with digits,
                # the recommendation should produce a digits pattern.
                TranslatedDigitsPattern
            ),
            (
                "1.1",  # number
                # When a digit is combined with a number,
                # the recommendation should produce a number pattern.
                TranslatedNumberPattern
            ),
            (
                "-1.1", # mixed number
                # When a digit is combined with a mixed number,
                # the recommendation should produce a mixed number pattern.
                TranslatedMixedNumberPattern
            ),
            (
                "abc123",   # a word
                # When a digit is combined with a word,
                # the recommendation should produce a word pattern.
                TranslatedWordPattern
            ),
            (
                "a1 a12",   # words
                # When a digit is combined with words,
                # the recommendation should produce words pattern.
                TranslatedWordsPattern
            ),
            (
                "abc.123",  # a mixed word
                # When a digit is combined with a mixed word,
                # the recommendation should produce a mixed word pattern.
                TranslatedMixedWordPattern
            ),
            (
                "a.1 b.1",  # mixed words
                # When a digit is combined with mixed words,
                # the recommendation should produce mixed words pattern.
                TranslatedMixedWordsPattern
            ),
            (
                "abc\xc8",  # non-whitespaces
                # When a digit is combined with non-whitespaces,
                # the recommendation should produce non-whitespaces pattern.
                TranslatedNonWhitespacesPattern
            ),
            (
                "abc\xc8 xyz",  # non-whitespace group
                # When a digit is combined with non-whitespaces,
                # the recommendation should produce non-whitespace group pattern.
                TranslatedNonWhitespacesGroupPattern
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
        recommend_instance = self.digits_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "1",    # digit
                # When digits are combined with a digit,
                # the recommendation should produce digits pattern.
                TranslatedDigitsPattern
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that a digit type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.digits_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "ab",  # letters
                # When a digit is combined with letters,
                # the recommendation should produce a word pattern.
                TranslatedWordPattern
            ),
            (
                "+",  # a punctuation
                # When a digit is combined with a punctuation,
                # the recommendation should produce a punctuation pattern.
                TranslatedNonWhitespacesPattern
            ),
            (
                "++",  # punctuations
                # When a digit is combined with punctuations,
                # the recommendation should produce punctuations pattern.
                TranslatedNonWhitespacesPattern
            ),
            (
                "++ -- ==",  # punctuation group
                # When a digit is combined with punctuation group,
                # the recommendation should produce punctuation group pattern.
                TranslatedNonWhitespacesGroupPattern
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
        recommend_instance = self.digits_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)

    def test_raise_exception_in_is_subset_of(self):
        """
        Verify that `is_subset_of` raises a NotImplementRecommendedRTPattern
        when called with an unsupported dummy pattern.
        """
        dummy_other = TranslatedDummyPattern()
        with pytest.raises(Exception) as ex:
            self.digits_node.is_subset_of(dummy_other)
        assert ex.type.__name__ == "NotImplementRecommendedRTPattern"

    def test_raise_exception_in_is_superset_of(self):
        """
        Verify that `is_superset_of` raises a NotImplementRecommendedRTPattern
        when called with an unsupported dummy pattern.
        """
        dummy_other = TranslatedDummyPattern()
        with pytest.raises(Exception) as ex:
            self.digits_node.is_superset_of(dummy_other)
        assert ex.type.__name__ == "NotImplementRecommendedRTPattern"

    def test_raise_exception_in_recommend(self):
        """
        Verify that `recommend` raises a NotImplementRecommendedRTPattern
        when called with an unsupported dummy pattern.
        """
        dummy_other = TranslatedDummyPattern()
        with pytest.raises(Exception) as ex:
            self.digits_node.recommend(dummy_other)
        assert ex.type.__name__ == "NotImplementRecommendedRTPattern"
