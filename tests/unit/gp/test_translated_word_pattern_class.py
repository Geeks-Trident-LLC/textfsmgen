"""
Unit tests for the `textfsmgen.gp.TranslatedWordPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_word_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_word_pattern_class.py
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
TranslatedWordPattern,
TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
# TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedWordPatternClass:
    """Test suite for TranslatedWordPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedWordPattern instance for reuse."""
        self.word_node = TranslatedWordPattern("abc123")

    @pytest.mark.parametrize(
        "other",
        [
            "abc123",           # word is a subset of word
            "a1 b2"             # word is a subset of words
            "abc.123",          # word is a subset of mixed-word
            "a.1 b.2",          # word is a subset of mixed-words
            "abc\xc8",          # word is a subset of non-whitespaces
            "abc\xc8 xyz",      # word is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that word data is a subset of (word(s), mixed-word(s), non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.word_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # word is not a subset of punct
            "--++==",           # word is not a subset of puncts
            "-- ++ ==",         # word is not a subset of punct-group
            "1.1",              # word is not a subset of number
            "-1.1",             # word is not a subset of mixed-number
            ["a", "1", "#"],    # word is not a subset of graph
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that word data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.word_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # word is a superset of letter
            "abc",              # word is a superset of letters
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that word data is a superset of (letter(s)).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.word_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc123",               # word
                TranslatedWordPattern   # (word, word) => word
            ),
            (
                "a1 b2",                # words
                TranslatedWordsPattern  # (word, words) => words
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (word, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (word, mixed-words) => mixed-words
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (word, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (word, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that word type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.word_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                    # letter
                TranslatedWordPattern   # (word, letter) => word
            ),
            (
                "abc",                  # letters
                TranslatedWordPattern   # (word, letters) => word
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that word type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.word_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                ["a", "1", "#"],                # graph
                TranslatedNonWhitespacesPattern # (word, graph) => non-whitespaces
            ),
            (
                "1",                            # digit
                TranslatedNonWhitespacesPattern # (word, digit) => non-whitespaces
            ),
            (
                "123",                          # digits
                TranslatedNonWhitespacesPattern # (word, digits) => non-whitespaces
            ),
            (
                "1.1",                          # number
                TranslatedNonWhitespacesPattern # (word, number) => non-whitespaces
            ),
            (
                "-1.1",                         # mixed-number
                TranslatedNonWhitespacesPattern # (word, mixed-number) => non-whitespaces
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacesPattern # (word, non-whitespace) => non-whitespaces
            ),
            (
                "-",                            # punct
                TranslatedNonWhitespacesPattern # (word, non-whitespace) => non-whitespaces
            ),
            (
                "--++==",                       # puncts
                TranslatedNonWhitespacesPattern # (word, puncts) => non-whitespaces
            ),
            (
                "-- ++ ==",                             # punct-group
                TranslatedNonWhitespacesGroupPattern    # (word, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that word type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.word_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
