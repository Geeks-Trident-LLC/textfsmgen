"""
Unit tests for the `textfsmgen.gp.TranslatedPunctPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_punct_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_punct_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
# TranslatedDigitPattern,
# TranslatedDigitsPattern,
# TranslatedNumberPattern,
# TranslatedMixedNumberPattern,
# TranslatedLetterPattern,
# TranslatedLettersPattern,
# TranslatedAlphabetNumericPattern,
TranslatedPunctPattern,
TranslatedPunctsPattern,
TranslatedPunctsGroupPattern,
TranslatedGraphPattern,
# TranslatedWordPattern,
# TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedPunctPatternClass:
    """Test suite for TranslatedPunctPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedPunctPattern instance for reuse."""
        self.punct_node = TranslatedPunctPattern("-")

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # punct is a subset of punct
            ["a", "1", "#"],    # punct is a subset of graph
            "==",               # punct is a subset of puncts
            "-- ++ =="          # punct is a subset of punct-group
            "abc.123",          # punct is a subset of mixed-word
            "a.1 b.2",          # punct is a subset of mixed-words
            "\xc8",             # punct is a subset of non-whitespace
            "abc\xc8",          # punct is a subset of non-whitespaces
            "abc\xc8 xyz",      # punct is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that punctuation data is a subset of (punct(s)(-group),
        graph, mixed-word(s), non-whitespace(s)(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.punct_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # punct is not a subset of digit
            "123",              # punct is not a subset of digits
            "1.1",              # punct is not a subset of number
            "-1.1",             # punct is not a subset of mixed-number
            "a",                # punct is not a subset of letter
            "abc",              # punct is not a subset of letters
            "abc123",           # punct is not a subset of word
            "a1 b1",            # punct is not a subset of words

        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that punctuation data is not a subset of (digits, number,
        mixed-number, letter(s), word(s))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.punct_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # punct is not a superset of letter
            "1",                # punct is not a superset of digit
            ["a", "1"],         # punct is not a superset of alpha-num
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that punctuation data does not have any superset.
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.punct_node.is_superset_of(other_instance) is False

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-",                    # punct
                TranslatedPunctPattern  # (punct, punct) => punct
            ),
            (
                "--++==",               # puncts
                TranslatedPunctsPattern # (punct, puncts) => puncts
            ),
            (
                "-- ++ ==",                  # punct-group
                TranslatedPunctsGroupPattern # (punct, punct-group) => punct-group
            ),
            (
                ["a", "1", "#"],            # graph
                TranslatedGraphPattern      # (punct, graph) => graph
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (punct, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (punct, mixed-words) => mixed-words
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacePattern # (punct, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (punct, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (punct, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that punctuation type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.punct_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                    # letter
                TranslatedGraphPattern  # (punct, letter) => graph
            ),
            (
                "1",                    # digit
                TranslatedGraphPattern  # (punct, digit) => graph
            ),
            (
                ["a", "1"],             # alpha-num
                TranslatedGraphPattern  # (punct, alpha-num) => graph
            ),

            (
                "abc",                          # letters
                TranslatedNonWhitespacesPattern # (punct, letters) => non-whitespaces
            ),
            (
                "123",                          # digits
                TranslatedNonWhitespacesPattern # (punct, digits) => non-whitespaces
            ),
            (
                "1.1",                          # number
                TranslatedNonWhitespacesPattern # (punct, number) => non-whitespaces
            ),
            (
                "-1.1",                         # mixed-number
                TranslatedNonWhitespacesPattern # (punct, mixed-number) => non-whitespaces
            ),
            (
                "abc123",                       # word
                TranslatedNonWhitespacesPattern # (punct, word) => non-whitespaces
            ),
            (
                "a1 b1",                                # words
                TranslatedNonWhitespacesGroupPattern    # (punct, words) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that punctuation type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.punct_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
