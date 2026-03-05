"""
Unit tests for the `textfsmgen.gp.TranslatedMixedWordsPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_mixed_word_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_mixed_word_pattern_class.py
"""

import pytest

from textfsmgen.engine.gp import (
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
# TranslatedMixedWordPattern,
    TranslatedMixedWordsPattern,
# TranslatedNonWSPattern,
# TranslatedNonWSSPattern,
    TranslatedNonWSSGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedMixedWordsPatternClass:
    """Test suite for TranslatedMixedWordsPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedMixedWordsPattern instance for reuse."""
        self.mixed_words_node = TranslatedMixedWordsPattern("a.1 b.2")

    @pytest.mark.parametrize(
        "other",
        [
            "a.1 b.2",          # mixed-words are a subset of mixed-words
            "abc\xc8 xyz",      # mixed-words are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that mixed-words data is a subset of (mixed-words, non-whitespaces-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_words_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # mixed-words are not a subset of punct
            "--++==",           # mixed-words are not a subset of puncts
            "-- ++ ==",         # mixed-words are not a subset of punct-group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that mixed-words data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_words_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # mixed-words are a superset of letter
            "abc",              # mixed-words are a superset of letters
            "1",                # mixed-words are a superset of digit
            "123",              # mixed-words are a superset of digits
            "1.1",              # mixed-words are a superset of number
            "-1.1",             # mixed-words are a superset of mixed-number
            ["a", "1"],         # mixed-words are a superset of alpha-num
            "abc123",           # mixed-words are a superset of word
            "a1 b2",            # mixed-words are a superset of words
            "a.1",              # mixed-words are a superset of mixed-word
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that mixed-words data is a superset of (letter(s), digit(s),
        number, mixed-number, alpha-num, word).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.mixed_words_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (mixed-words, mixed-words) => mixed-words
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                TranslatedNonWSSGroupPattern    # (mixed-words, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that mixed-words type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_words_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                        # letter
                TranslatedMixedWordsPattern # (mixed-words, letter) => mixed-words
            ),
            (
                "abc",                      # letters
                TranslatedMixedWordsPattern # (mixed-words, letters) => mixed-words
            ),
            (
                "1",                        # digit
                TranslatedMixedWordsPattern # (mixed-words, digit) => mixed-words
            ),
            (
                "123",                      # digits
                TranslatedMixedWordsPattern # (mixed-words, digits) => mixed-words
            ),
            (
                "1.1",                      # number
                TranslatedMixedWordsPattern # (mixed-words, number) => mixed-words
            ),
            (
                "-1.1",                     # mixed-number
                TranslatedMixedWordsPattern # (mixed-words, mixed-number) => mixed-word
            ),
            (
                ["a", "1"],                 # alpha-num
                TranslatedMixedWordsPattern # (mixed-words, alpha-num) => mixed-word
            ),
            (
                "abc123",                   # word
                TranslatedMixedWordsPattern # (mixed-words, word) => mixed-word
            ),
            (
                "a1 b1",                    # words
                TranslatedMixedWordsPattern # (mixed-words, words) => mixed-words
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordsPattern # (mixed-words, mixed-word) => mixed-words
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that mixed-words type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_words_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                    ["a", "1", "#"],  # graph
                    TranslatedNonWSSGroupPattern    # (mixed-words, graph) => non-whitespaces-group
            ),
            (
                "\xc8",  # non-whitespace
                TranslatedNonWSSGroupPattern    # (mixed-words, non-whitespace) => non-whitespaces-group
            ),
            (
                "abc\xc8",  # non-whitespaces
                TranslatedNonWSSGroupPattern    # (mixed-words, non-whitespaces) => non-whitespaces-group
            ),
            (
                "-",  # punct
                TranslatedNonWSSGroupPattern    # (mixed-words, non-whitespace) => non-whitespaces-group
            ),
            (
                "--++==",  # puncts
                TranslatedNonWSSGroupPattern    # (mixed-words, puncts) => non-whitespaces-group
            ),
            (
                "-- ++ ==",  # punct-group
                TranslatedNonWSSGroupPattern    # (mixed-words, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that mixed-words type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.mixed_words_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
