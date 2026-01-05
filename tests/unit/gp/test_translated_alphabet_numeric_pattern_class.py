"""
Unit tests for the `textfsmgen.gp.TranslatedAlphabetNumericPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_alphabet_numeric_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_alphabet_numeric_pattern_class.py
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


class TestTranslatedAlphabetNumericPatternClass:
    """Test suite for TranslatedAlphabetNumericPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedAlphabetNumericPattern instance for reuse."""
        self.alphabet_numeric_node = TranslatedAlphabetNumericPattern("a", "1")

    @pytest.mark.parametrize(
        "other",
        [
            ["a", "1"],         # alpha-num is a subset of alpha-num
            ["a", "1", "#"],    # alpha-num is a subset of graph
            "abc123",           # alpha-num is a subset of word
            "a1 b12",           # alpha-num is a subset of words
            "abc.123",          # alpha-num is a subset of mixed word
            "a.1 b.2",          # alpha-num is a subset of mixed words
            "\xc8",             # alpha-num is a subset of non-whitespace
            "abc\xc8",          # alpha-num is a subset of non-whitespaces
            "abc\xc8 xyz",      # alpha-num is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that alpha-num data is a subset of (alpha-num, graph, word(s),
        mixed-word(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.alphabet_numeric_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "123",              # alpha-num is not a subset of digits
            "1.1",              # alpha-num is not a subset of number
            "-1.1",             # alpha-num is not a subset of mixed-number
            "++--",             # alpha-num is not a subset of punctuation(s)
            "++ -- ==",         # alpha-num is not a subset of punctuation group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that alpha-num data is not a subset of (digits, number,
        mixed-number, punctuation(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.alphabet_numeric_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # alpha-num is a superset of letter
            "1",                # alpha-num is a superset of digit
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that alpha-num data is a subset of (letter, digit).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.alphabet_numeric_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                ["a", "1"],                         # alpha-num
                TranslatedAlphabetNumericPattern    # (alpha-num, alpha-num) => alpha-num
            ),
            (
                "abc123",               # a word
                TranslatedWordPattern   # (alpha-num, word) => word
            ),
            (
                "a1 a12",               # words
                TranslatedWordsPattern  # (alpha-num, words) => words
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (alpha-num, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (alpha-num, mixed-words) => mixed-words
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacePattern # (alpha-num, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (alpha-num, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (alpha-num, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that alpha-num type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.alphabet_numeric_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                                # letter
                TranslatedAlphabetNumericPattern    # (alpha-num, letter) => alpha-num
            ),
            (
                "1",                                # letter
                TranslatedAlphabetNumericPattern    # (alpha-num, letter) => alpha-num
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that alpha-num type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.alphabet_numeric_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "123",                  # digits
                TranslatedWordPattern   # (alpha-num, digits) => word
            ),
            (
                "1.1",                      # number
                TranslatedMixedWordPattern  # (alpha-num, number) => mixed-word
            ),
            (
                "-1.1",                     # mixed-number
                TranslatedMixedWordPattern  # (alpha-num, mixed-number) => mixed-word
            ),
            (
                "+",                            # punctuation
                TranslatedNonWhitespacePattern # (alpha-num, punct) => non-whitespace
            ),
            (
                "++",                           # punctuations
                TranslatedNonWhitespacesPattern # (alpha-num, puncts) => non-whitespaces
            ),
            (
                "++ -- ==",                             # punctuation-group
                TranslatedNonWhitespacesGroupPattern    # (alpha-num, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that alpha-num type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.alphabet_numeric_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
