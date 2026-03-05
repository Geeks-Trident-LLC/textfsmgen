"""
Unit tests for the `textfsmgen.gp.TranslatedNonWSPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_non_whitespace_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_non_whitespace_pattern_class.py
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
# TranslatedMixedWordsPattern,
    TranslatedNonWSPattern,
    TranslatedNonWSSPattern,
    TranslatedNonWSSGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedNonWhitespacePatternClass:
    """Test suite for TranslatedNonWSPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedNonWSPattern instance for reuse."""
        self.non_whitespace_node = TranslatedNonWSPattern("\xc8")

    @pytest.mark.parametrize(
        "other",
        [
            "\xc8",             # non-whitespace is a subset of non-whitespace
            "abc\xc8",          # non-whitespace is a subset of non-whitespaces
            "abc\xc8 xyz",      # non-whitespace is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that non-whitespace data is a subset of (non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.non_whitespace_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "--++==",           # non-whitespace is not a subset of puncts
            "-- ++ ==",         # non-whitespace is not a subset of punct-group
            "1.1",              # non-whitespace is not a subset of number
            "-1.1",             # non-whitespace is not a subset of mixed-number
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that non-whitespace data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.non_whitespace_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # non-whitespace is a superset of letter
            "1",                # non-whitespace is a superset of digit
            ["a", "1"],         # non-whitespace is a superset of alpha-num
            "-",                # non-whitespace is a superset of digit
            ["a", "1", "#"],    # non-whitespace is a superset of graph
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that non-whitespace data is a superset of (letter(s)).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.non_whitespace_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "\xc8",  # non-whitespace
                TranslatedNonWSPattern  # (non-whitespace, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",  # non-whitespaces
                TranslatedNonWSSPattern # (non-whitespace, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                TranslatedNonWSSGroupPattern    # (non-whitespace, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that non-whitespace type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.non_whitespace_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",  # letter
                TranslatedNonWSPattern  # (non-whitespace, letter) => non-whitespace
            ),
            (
                "1",  # digit
                TranslatedNonWSPattern  # (non-whitespace, digit) => non-whitespace
            ),
            (
                    ["a", "1"],  # alpha-num
                    TranslatedNonWSPattern  # (non-whitespace, alpha-num) => non-whitespace
            ),
            (
                "-",  # punct
                TranslatedNonWSPattern  # (non-whitespace, punct) => non-whitespace
            ),
            (
                    ["a", "1", "#"],  # graph
                    TranslatedNonWSPattern  # (non-whitespace, graph) => non-whitespace
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that non-whitespace type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.non_whitespace_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc",  # letters
                TranslatedNonWSSPattern # (non-whitespace, letters) => non-whitespaces
            ),
            (
                "123",  # digits
                TranslatedNonWSSPattern # (non-whitespace, digit) => non-whitespaces
            ),
            (
                "--++==",  # puncts
                TranslatedNonWSSPattern # (non-whitespace, puncts) => non-whitespaces
            ),
            (
                "1.1",  # number
                TranslatedNonWSSPattern # (non-whitespace, number) => non-whitespaces
            ),
            (
                "-1.1",  # mixed-number
                TranslatedNonWSSPattern # (non-whitespace, mixed-number) => non-whitespaces
            ),
            (
                "abc123",  # word
                TranslatedNonWSSPattern # (non-whitespace, word) => non-whitespaces
            ),
            (
                "abc.123",  # mixed-word
                TranslatedNonWSSPattern # (non-whitespace, mixed-word) => non-whitespaces
            ),
            (
                "a1 b1",  # words
                TranslatedNonWSSGroupPattern # (non-whitespace, words) => non-whitespaces-group
            ),
            (
                "a.1 b.1",  # mixed-words
                TranslatedNonWSSGroupPattern # (non-whitespace, mixed-words) => non-whitespaces-group
            ),
            (
                "-- ++ ==",  # punct-group
                TranslatedNonWSSGroupPattern    # (non-whitespace, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that non-whitespace type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.non_whitespace_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
