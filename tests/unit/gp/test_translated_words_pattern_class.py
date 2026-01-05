"""
Unit tests for the `textfsmgen.gp.TranslatedWordsPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_words_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_words_pattern_class.py
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
# TranslatedPunctPattern,
# TranslatedPunctsPattern,
# TranslatedPunctsGroupPattern,
# TranslatedGraphPattern,
# TranslatedWordPattern,
TranslatedWordsPattern,
# TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
# TranslatedNonWhitespacePattern,
# TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedWordsPatternClass:
    """Test suite for TranslatedWordsPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedWordsPattern instance for reuse."""
        self.words_node = TranslatedWordsPattern("abc123")

    @pytest.mark.parametrize(
        "other",
        [
            "a1 b2"             # words are a subset of words
            "a.1 b.2",          # words are a subset of mixed-words
            "abc\xc8 xyz",      # words are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that words data is a subset of (word(s), mixed-word(s), non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.words_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # words are not a subset of punct
            "--++==",           # words are not a subset of puncts
            "-- ++ ==",         # words are not a subset of punct-group
            "1.1",              # words are not a subset of number
            "-1.1",             # words are not a subset of mixed-number
            ["a", "1", "#"],    # words are not a subset of graph
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that words data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.words_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # words are a superset of letter
            "abc",              # words are a superset of letters
            "abc123",           # words are a superset of word
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that words data is a superset of (letter(s), word).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.words_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a1 b2",                # words
                TranslatedWordsPattern  # (words, words) => words
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (words, mixed-words) => mixed-words
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (words, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that words type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.words_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                    # letter
                TranslatedWordsPattern  # (words, letter) => words
            ),
            (
                "abc",                  # letters
                TranslatedWordsPattern  # (words, letters) => words
            ),
            (
                "abc123",               # word
                TranslatedWordsPattern  # (words, word) => words
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that words type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.words_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                ["a", "1"],                             # alpha-num
                TranslatedNonWhitespacesGroupPattern    # (words, alpha-num) => non-whitespaces-group
            ),
            (
                ["a", "1", "#"],                        # graph
                TranslatedNonWhitespacesGroupPattern    # (words, graph) => non-whitespaces-group
            ),
            (
                "1",                                    # digit
                TranslatedNonWhitespacesGroupPattern    # (words, digit) => non-whitespaces-group
            ),
            (
                "123",                                  # digits
                TranslatedNonWhitespacesGroupPattern    # (words, digits) => non-whitespaces-group
            ),
            (
                "1.23",                                 # number
                TranslatedNonWhitespacesGroupPattern    # (words, number) => non-whitespaces-group
            ),
            (
                "-1.1",                                 # mixed-number
                TranslatedNonWhitespacesGroupPattern    # (words, mixed-number) => non-whitespaces-group
            ),
            (
                "\xc8",                                 # non-whitespace
                TranslatedNonWhitespacesGroupPattern    # (words, non-whitespace) => non-whitespaces-group
            ),
            (
                "-",                                    # punct
                TranslatedNonWhitespacesGroupPattern    # (words, non-whitespace) => non-whitespaces-group
            ),
            (
                "--++==",                               # puncts
                TranslatedNonWhitespacesGroupPattern    # (words, puncts) => non-whitespaces-group
            ),
            (
                "-- ++ ==",                             # punct-group
                TranslatedNonWhitespacesGroupPattern    # (words, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that words type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.words_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
