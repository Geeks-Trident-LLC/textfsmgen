"""
Unit tests for the `textfsmgen.gp.TranslatedLetterPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_letter_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_letter_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
# TranslatedDigitPattern,
# TranslatedDigitsPattern,
# TranslatedNumberPattern,
# TranslatedMixedNumberPattern,
TranslatedLetterPattern,
TranslatedLettersPattern,
TranslatedAlphabetNumericPattern,
# TranslatedPunctPattern,
# TranslatedPunctsPattern,
# TranslatedPunctsGroupPattern,
TranslatedGraphPattern,
TranslatedWordPattern,
TranslatedWordsPattern,
TranslatedMixedWordPattern,
TranslatedMixedWordsPattern,
TranslatedNonWhitespacePattern,
TranslatedNonWhitespacesPattern,
TranslatedNonWhitespacesGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedLetterPatternClass:
    """Test suite for TranslatedLetterPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedLetterPattern instance for reuse."""
        self.letter_node = TranslatedLetterPattern("a" "b", "c")

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # a letter is a subset of letter
            "ab",                # a letter is a subset of letters
            ["a", "1"],         # a letter is a subset of alphabet numeric
            ["a", "1", "#"],    # a letter is a subset of graph
            "abc123",           # a letter is a subset of word
            "a1 b12",           # a letter is a subset of words
            "abc.123",          # a letter is a subset of mixed word
            "a.1 b.2",          # a letter is a subset of mixed words
            "\xc8",             # a letter is a subset of non-whitespace
            "abc\xc8",          # a letter is a subset of non-whitespaces
            "abc\xc8 xyz",      # a letter is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
                    other.is_letter(),
            other.is_letters(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        Verify that a letter data is a subset of (letter(s), alphabet-numeric,
        graph, word(s), mixed-word(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.letter_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # a letter is not a subset of digit
            "123",              # a letter is not a subset of digits
            "1.1",              # a letter is not a subset of number
            "-1.1",             # a letter is not a subset of mixed-number
            "++--",             # a letter is not a subset of punctuation(s)
            "++ -- ==",         # a letter is not a subset of punctuation group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that a letter data is not a subset of (letter(s), number,
        mixed-number, punctuation(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.letter_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # a letter is not a superset of digit
            "123",              # a letter is not a superset of digits
            "1.1",              # a letter is not a superset of number
            "abc\xc8 xyz",      # a letter is not a superset of non-whitespace group
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that a letter data is correctly identified as not belonging
        to any broader translated category.
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.letter_node.is_superset_of(other_instance) is False

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                        # letter
                TranslatedLetterPattern     # (letter, letter) => letter
            ),
            (
                "abc",                      # letters
                TranslatedLettersPattern    # (letter, letters) => letters
            ),
            (
                ["a", "1"],                         # alphabet-numeric
                TranslatedAlphabetNumericPattern    # (letter, alphabet-numeric) => alphabet-numeric
            ),
            (
                ["a", "1", "#"],        # graph
                TranslatedGraphPattern  # (letter, graph) => graph
            ),
            (
                "abc123",               # a word
                TranslatedWordPattern   # (letter, word) => word
            ),
            (
                "a1 a12",               # words
                TranslatedWordsPattern  # (letter, words) => words
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (letter, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (letter, mixed-words) => mixed-words
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacePattern  # (letter, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (letter, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (letter, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that a letter type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.letter_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "1",                                # digit
                TranslatedAlphabetNumericPattern    # (letter, digit) => alphabet-numeric
            ),
            (
                "123",                  # digits
                TranslatedWordPattern   # (letter, digits) => digits
            ),
            (
                "1.1",                      # number
                TranslatedMixedWordPattern  # (letter, number) => mixed-word
            ),
            (
                "-1.1",                     # mixed-number
                TranslatedMixedWordPattern  # (letter, mixed-number) => mixed-word
            ),
            (
                "+",                        # punctuation
                TranslatedGraphPattern      # (letter, punct) => punct
            ),
            (
                "++",                           # punctuations
                TranslatedNonWhitespacesPattern # (letter, puncts) => non-whitespaces
            ),
            (
                "++ -- ==",                             # punctuation-group
                TranslatedNonWhitespacesGroupPattern    # (letter, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that a letter type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.letter_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)