"""
Unit tests for the `textfsmgen.gp.TranslatedPunctsPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_puncts_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_puncts_pattern_class.py
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
TranslatedPunctsPattern,
TranslatedPunctsGroupPattern,
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


class TestTranslatedPunctsPatternClass:
    """Test suite for TranslatedPunctsPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedPunctsPattern instance for reuse."""
        self.puncts_node = TranslatedPunctsPattern("--")

    @pytest.mark.parametrize(
        "other",
        [
            "==",               # puncts are a subset of puncts
            "-- ++ =="          # puncts are a subset of punct-group
            "abc.123",          # puncts are a subset of mixed-word
            "a.1 b.2",          # puncts are a subset of mixed-words
            "abc\xc8",          # puncts are a subset of non-whitespaces
            "abc\xc8 xyz",      # puncts are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that punctuations data is a subset of (punct(s)(-group),
        mixed-word(s), non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.puncts_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # puncts are not a subset of digit
            "123",              # puncts are not a subset of digits
            "1.1",              # puncts are not a subset of number
            "-1.1",             # puncts are not a subset of mixed-number
            "a",                # puncts are not a subset of letter
            "abc",              # puncts are not a subset of letters
            "abc123",           # puncts are not a subset of word
            "a1 b1",            # puncts are not a subset of words

        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that punctuations data is not a subset of (digits, number,
        mixed-number, letter(s), word(s))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.puncts_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            ".",                # puncts are a superset of punct
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that punctuations data is a superset of (punct).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.puncts_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "--++==",               # puncts
                TranslatedPunctsPattern # (puncts, puncts) => puncts
            ),
            (
                "-- ++ ==",                  # punct-group
                TranslatedPunctsGroupPattern # (puncts, punct-group) => punct-group
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (puncts, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (puncts, mixed-words) => mixed-words
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (puncts, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (puncts, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that punctuations type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.puncts_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-",                    # punct
                TranslatedPunctsPattern # (puncts, punct) => punct
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that punctuations type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.puncts_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                            # letter
                TranslatedNonWhitespacesPattern # (puncts, letter) => non-whitespaces
            ),
            (
                "1",                            # digit
                TranslatedNonWhitespacesPattern # (puncts, digit) => non-whitespaces
            ),
            (
                ["a", "1"],                     # alpha-num
                TranslatedNonWhitespacesPattern # (puncts, alpha-num) => non-whitespaces
            ),
            (
                ["a", "1", "#"],                # graph
                TranslatedNonWhitespacesPattern # (puncts, graph) => non-whitespaces
            ),
            (
                "abc",                          # letters
                TranslatedNonWhitespacesPattern # (puncts, letters) => non-whitespaces
            ),
            (
                "123",                          # digits
                TranslatedNonWhitespacesPattern # (puncts, digits) => non-whitespaces
            ),
            (
                "1.1",                          # number
                TranslatedNonWhitespacesPattern # (puncts, number) => non-whitespaces
            ),
            (
                "-1.1",                         # mixed-number
                TranslatedNonWhitespacesPattern # (puncts, mixed-number) => non-whitespaces
            ),
            (
                "abc123",                       # word
                TranslatedNonWhitespacesPattern # (puncts, word) => non-whitespaces
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacesPattern # (puncts, non-whitespace) => non-whitespaces
            ),
            (
                "a1 b1",                                # words
                TranslatedNonWhitespacesGroupPattern    # (puncts, words) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that punctuations type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.puncts_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
