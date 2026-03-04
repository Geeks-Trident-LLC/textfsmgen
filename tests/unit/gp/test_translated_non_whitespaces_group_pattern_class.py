"""
Unit tests for the `textfsmgen.gp.TranslatedNonWSSGroupPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_non_whitespaces_group_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_non_whitespaces_group_pattern_class.py
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
# TranslatedMixedWordPattern,
# TranslatedMixedWordsPattern,
# TranslatedNonWSPattern,
# TranslatedNonWSSPattern,
    TranslatedNonWSSGroupPattern
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestTranslatedNonWhitespacesGroupPatternClass:
    """Test suite for TranslatedNonWSSGroupPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedNonWSSGroupPattern instance for reuse."""
        self.non_whitespaces_group_node = TranslatedNonWSSGroupPattern("abc\xc8 xyz")

    @pytest.mark.parametrize(
        "other",
        [
            "abc\xc8 xyz",      # non-whitespaces are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that word data is a subset of (non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.non_whitespaces_group_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "abc 123",          # non-whitespaces are not a subset of words
            "a.1 b.2",          # non-whitespaces are not a subset of mixed-words
            "-- ++ ==",         # non-whitespaces are not a subset of punct-group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that word data is not a subset of (puncts-group, words,
        mixed-words, non-whitespaces-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.non_whitespaces_group_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # non-whitespaces are a superset of letter
            "abc",              # non-whitespaces are a superset of letters
            "1",                # non-whitespaces are a superset of digit
            "123",              # non-whitespaces are a superset of digits
            "1.1",              # non-whitespaces are a superset of number
            "-1,1",             # non-whitespaces are a superset of mixed-number
            ["a", "1"],         # non-whitespaces are a superset of alpha-num
            ["a", "1", "#"],    # non-whitespaces are a superset of graph
            "-",                # non-whitespaces are a superset of punct
            "---++==",          # non-whitespaces are a superset of puncts
            "--- ++ ==",        # non-whitespaces are a superset of puncts-group
            "abc123",           # non-whitespaces are a superset of word
            "a1 b2",            # non-whitespaces are a superset of words
            "abc.123",          # non-whitespaces are a superset of mixed-word
            "a.1 b.2",          # non-whitespaces are a superset of mixed-words
            "\xc8",             # non-whitespaces are a superset of non-whitespace
            "abc\xc8",          # non-whitespaces are a superset of non-whitespaces
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that word data is a superset of (letter(s)).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.non_whitespaces_group_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (   # (non-whitespaces-group, non-whitespace-group) => non-whitespace-group
                    "abc\xc8 xyz",  # non-whitespace-group
                    TranslatedNonWSSGroupPattern
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
        recommend_instance = self.non_whitespaces_group_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (   # (non-whitespaces-group, letter) => non-whitespaces-group
                    "a",  # letter
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, letters) => non-whitespaces-group
                    "abc",  # letters
                    TranslatedNonWSSGroupPattern
            ),
            (   ## (non-whitespaces, digit) => non-whitespaces-group
                    "1",  # digit
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, digits) => non-whitespaces-group
                    "123",  # digits
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, number) => non-whitespaces-group
                    "1.1",  # number
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, mixed-number) => non-whitespaces-group
                    "-1.1",  # mixed-number
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, alpha-num) => non-whitespaces-group
                    ["a", "1"],  # alpha-num
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, graph) => non-whitespaces-group
                    ["a", "1", "#"],  # graph
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, punct) => non-whitespaces-group
                    "-",  # punct
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, puncts) => non-whitespaces-group
                    "--++==",  # puncts
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, puncts-group) => non-whitespaces-group
                    "-- ++ ==",  # puncts-group
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, word) => non-whitespaces-group
                    "abc123",  # word
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, words) => non-whitespaces-group
                    "a1 b2",  # words
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, mixed-word) => non-whitespaces-group
                    "abc.123",  # mixed-word
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, mixed-words) => non-whitespaces-group
                    "a.1 b.2",  # mixed-words
                    TranslatedNonWSSGroupPattern
            ),
            (   # (non-whitespaces, non-whitespace) => non-whitespaces-group
                    "\xc8",  # non-whitespace
                    TranslatedNonWSSGroupPattern
            ),
            (  # (non-whitespaces, non-whitespaces) => non-whitespaces-group
                    "abc\xc8",  # non-whitespaces
                    TranslatedNonWSSGroupPattern
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
        recommend_instance = self.non_whitespaces_group_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True
