"""
Unit tests for the `textfsmgen.gp.TranslatedPunctsGroupPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_puncts_group_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_puncts_group_pattern_class.py
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
    TranslatedPunctsGroupPattern,
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


class TestTranslatedPunctsGroupPatternClass:
    """Test suite for TranslatedPunctsGroupPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedPunctsGroupPattern instance for reuse."""
        self.punct_group_node = TranslatedPunctsGroupPattern("-- ++ ==")

    @pytest.mark.parametrize(
        "other",
        [
            "-- ++ =="          # punct-group is a subset of punct-group
            "a.1 b.2",          # punct-group is a subset of mixed-words
            "abc\xc8 xyz",      # punct-group is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that punctuation-group data is a subset of (punct-group,
        mixed-words, non-whitespaces-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.punct_group_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # punct-group is not a subset of digit
            "123",              # punct-group is not a subset of digits
            "1.1",              # punct-group is not a subset of number
            "-1.1",             # punct-group is not a subset of mixed-number
            "a",                # punct-group is not a subset of letter
            "abc",              # punct-group is not a subset of letters
            "abc123",           # punct-group is not a subset of word
            "a1 b1",            # punct-group is not a subset of words
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that punctuation-group data is not a subset of (digits, number,
        mixed-number, letter(s), word(s))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.punct_group_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            ".",                # punct-group is a superset of punct
            "++==--",           # punct-group is a superset of puncts
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that punctuation-group data is a superset of (punct(s)).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.punct_group_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-- ++ ==",                  # punct-group
                TranslatedPunctsGroupPattern # (punct-group, punct-group) => punct-group
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (punct-group, mixed-words) => mixed-words
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                TranslatedNonWSSGroupPattern    # (punct-group, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that punctuation-group type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.punct_group_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-",                            # punct
                TranslatedPunctsGroupPattern    # (punct-group, punct) => punct-group
            ),
            (
                "--++==",                       # puncts
                TranslatedPunctsGroupPattern    # (punct-group, puncts) => punct-group
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that punctuation-group type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.punct_group_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",  # letter
                TranslatedNonWSSGroupPattern    # (punct-group, letter) => non-whitespace-group
            ),
            (
                "1",  # digit
                TranslatedNonWSSGroupPattern    # (punct-group, digit) => non-whitespace-group
            ),
            (
                    ["a", "1"],  # alpha-num
                    TranslatedNonWSSGroupPattern    # (punct-group, alpha-num) => non-whitespace-group
            ),
            (
                    ["a", "1", "#"],  # graph
                    TranslatedNonWSSGroupPattern    # (punct-group, graph) => non-whitespace-group
            ),
            (
                "abc",  # letters
                TranslatedNonWSSGroupPattern    # (punct-group, letters) => non-whitespace-group
            ),
            (
                "123",  # digits
                TranslatedNonWSSGroupPattern    # (punct-group, digits) => non-whitespace-group
            ),
            (
                "1.1",  # number
                TranslatedNonWSSGroupPattern    # (punct-group, number) => non-whitespace-group
            ),
            (
                "-1.1",  # mixed-number
                TranslatedNonWSSGroupPattern    # (punct-group, mixed-number) => non-whitespace-group
            ),
            (
                "abc123",  # word
                TranslatedNonWSSGroupPattern    # (punct-group, word) => non-whitespace-group
            ),
            (
                "a1 b1",  # words
                TranslatedNonWSSGroupPattern    # (punct-group, words) => non-whitespace-group
            ),
            (
                "\xc8",  # non-whitespace
                TranslatedNonWSSGroupPattern    # (punct-group, non-whitespace) => non-whitespace-group
            ),
            (
                "abc\xc8",  # non-whitespaces
                TranslatedNonWSSGroupPattern    # (punct-group, non-whitespaces) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that punctuation-group type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.punct_group_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
