"""
Unit tests for the `textfsmgen.gp.TranslatedMixedWordPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_mixed_word_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_mixed_word_pattern_class.py
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
# TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
# TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedMixedWordPatternClass:
    """Test suite for TranslatedMixedWordPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedMixedWordPattern instance for reuse."""
        self.mixed_word_node = TranslatedMixedWordPattern("abc.123")

    @pytest.mark.parametrize(
        "other",
        [
            "abc.123",          # mixed-word is a subset of mixed-word
            "a.1 b.2",          # mixed-word is a subset of mixed-words
            "abc\xc8",          # mixed-word is a subset of non-whitespaces
            "abc\xc8 xyz",      # mixed-word is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that mixed-word data is a subset of (word(s), mixed-word(s), non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_word_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # mixed-word is not a subset of punct
            "--++==",           # mixed-word is not a subset of puncts
            "-- ++ ==",         # mixed-word is not a subset of punct-group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that mixed-word data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_word_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # mixed-word is a superset of letter
            "abc",              # mixed-word is a superset of letters
            "1",                # mixed-word is a superset of digit
            "123",              # mixed-word is a superset of digits
            "1.1",              # mixed-word is a superset of number
            "-1.1",             # mixed-word is a superset of mixed-number
            ["a", "1"],         # mixed-word is a superset of alpha-num
            "abc123",           # mixed-word is a superset of word
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that mixed-word data is a superset of (letter(s), digit(s),
        number, mixed-number, alpha-num, word).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_word_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (mixed-word, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (mixed-word, mixed-words) => mixed-words
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (mixed-word, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (mixed-word, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that mixed-word type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_word_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                        # letter
                TranslatedMixedWordPattern  # (mixed-word, letter) => mixed-word
            ),
            (
                "abc",                      # letters
                TranslatedMixedWordPattern  # (mixed-word, letters) => mixed-word
            ),
            (
                "1",                        # digit
                TranslatedMixedWordPattern  # (mixed-word, digit) => mixed-word
            ),
            (
                "123",                      # digits
                TranslatedMixedWordPattern  # (mixed-word, digits) => mixed-word
            ),
            (
                "1.1",                      # number
                TranslatedMixedWordPattern  # (mixed-word, number) => mixed-word
            ),
            (
                "-1.1",                     # mixed-number
                TranslatedMixedWordPattern  # (mixed-word, mixed-number) => mixed-word
            ),
            (
                ["a", "1"],                 # alpha-num
                TranslatedMixedWordPattern  # (mixed-word, alpha-num) => mixed-word
            ),
            (
                "abc123",                   # word
                TranslatedMixedWordPattern  # (mixed-word, word) => mixed-word
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that mixed-word type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_word_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc xyz",                  # words
                TranslatedMixedWordsPattern # (mixed-word, words) => mixed-words
            ),
            (
                ["a", "1", "#"],                # graph
                TranslatedNonWhitespacesPattern # (mixed-word, graph) => non-whitespaces
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacesPattern # (mixed-word, non-whitespace) => non-whitespaces
            ),
            (
                "-",                            # punct
                TranslatedNonWhitespacesPattern # (mixed-word, non-whitespace) => non-whitespaces
            ),
            (
                "--++==",                       # puncts
                TranslatedNonWhitespacesPattern # (mixed-word, puncts) => non-whitespaces
            ),
            (
                "-- ++ ==",                             # punct-group
                TranslatedNonWhitespacesGroupPattern    # (mixed-word, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that mixed-word type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_word_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
