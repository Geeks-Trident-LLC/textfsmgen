"""
Unit tests for the `textfsmgen.gp.TranslatedLettersPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_letters_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_letters_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
# TranslatedDigitPattern,
# TranslatedDigitsPattern,
# TranslatedNumberPattern,
# TranslatedMixedNumberPattern,
# TranslatedLetterPattern,
TranslatedLettersPattern,
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


class TestTranslatedLettersPatternClass:
    """Test suite for TranslatedLettersPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedLettersPattern instance for reuse."""
        self.letters_node = TranslatedLettersPattern("abc")

    @pytest.mark.parametrize(
        "other",
        [
            "ab",               # letters are a subset of letters
            "abc123",           # letters are a subset of word
            "a1 b12",           # letters are a subset of words
            "abc.123",          # letters are a subset of mixed word
            "a.1 b.2",          # letters are a subset of mixed words
            "abc\xc8",          # letters are a subset of non-whitespaces
            "abc\xc8 xyz",      # letters are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that letters, data is a subset of (letters, word(s),
        mixed-word(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.letters_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # letters are not a subset of digit
            "123",              # letters are not a subset of digits
            "1.1",              # letters are not a subset of number
            "-1.1",             # letters are not a subset of mixed-number
            "++--",             # letters are not a subset of punctuation(s)
            "++ -- ==",         # letters are not a subset of punctuation group
            "\xc8",             # letters are not a subset of non-whitespace
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that letters, data is not a subset of (letter(s), number,
        mixed-number, punctuation(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.letters_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # letters are a superset of letter
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that letters, data is a subset of (letter).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.letters_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc",                      # letters
                TranslatedLettersPattern    # (letters, letters) => letters
            ),
            (
                "abc123",               # a word
                TranslatedWordPattern   # (letters, word) => word
            ),
            (
                "a1 a12",               # words
                TranslatedWordsPattern  # (letters, words) => words
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (letters, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (letters, mixed-words) => mixed-words
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacesPattern # (letters, non-whitespace) => non-whitespaces
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (letters, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (letters, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that letters, type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.letters_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                        # letter
                TranslatedLettersPattern    # (letters, letter) => letters
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that letters, type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.letters_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "1",                    # digit
                TranslatedWordPattern   # (letters, digit) => word
            ),
            (
                "123",                  # digits
                TranslatedWordPattern   # (letters, digits) => word
            ),
            (
                ["a", "1"],             # alpha-num
                TranslatedWordPattern   # (letters, alpha-num) => word
            ),
            (
                "1.1",                      # number
                TranslatedMixedWordPattern  # (letters, number) => mixed-word
            ),
            (
                "-1.1",                     # mixed-number
                TranslatedMixedWordPattern  # (letters, mixed-number) => mixed-word
            ),
            (
                ["a", "1", "#"],            # graph
                TranslatedMixedWordPattern  # (letters, graph) => mixed-word
            ),
            (
                "+",                            # punctuation
                TranslatedNonWhitespacesPattern # (letters, punct) => non-whitespaces
            ),
            (
                "++",                           # punctuations
                TranslatedNonWhitespacesPattern # (letters, puncts) => non-whitespaces
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacesPattern # (letters, non-whitespace) => non-whitespaces
            ),
            (
                "++ -- ==",                             # punctuation-group
                TranslatedNonWhitespacesGroupPattern    # (letters, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that letters, type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.letters_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
