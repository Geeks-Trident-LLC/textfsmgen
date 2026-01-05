"""
Unit tests for the `textfsmgen.gp.TranslatedGraphPattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gp/test_translated_graph_pattern_class.py
    or
    $ python -m pytest tests/unit/gp/test_translated_graph_pattern_class.py
"""

import pytest

from textfsmgen.gp import (
TranslatedPattern,
TranslatedDigitPattern,
TranslatedDigitsPattern,
TranslatedNumberPattern,
TranslatedMixedNumberPattern,
TranslatedLetterPattern,
TranslatedLettersPattern,
TranslatedAlphabetNumericPattern,
TranslatedPunctPattern,
TranslatedPunctsPattern,
TranslatedPunctsGroupPattern,
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


class TestTranslatedGraphPatternClass:
    """Test suite for TranslatedGraphPattern class."""

    def setup_method(self):
        """Create a baseline TranslatedGraphPattern instance for reuse."""
        self.graph_node = TranslatedGraphPattern("a", "1", "#")

    @pytest.mark.parametrize(
        "other",
        [
            ["a", "1", "#"],    # graph is a subset of graph
            "abc.123",          # graph is a subset of mixed word
            "a.1 b.2",          # graph is a subset of mixed words
            "\xc8",             # graph is a subset of non-whitespace
            "abc\xc8",          # graph is a subset of non-whitespaces
            "abc\xc8 xyz",      # graph is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that graph data is a subset of (mixed-word(s), non-whitespace(s)(-group))
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.graph_node.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "123",              # graph is not a subset of digits
            "1.1",              # graph is not a subset of number
            "-1.1",             # graph is not a subset of mixed-number
            "++--",             # graph is not a subset of punctuation(s)
            "++ -- ==",         # graph is not a subset of punctuation group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that graph data is not a subset of (digits, number,
        mixed-number, punctuation(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.graph_node.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # graph is a superset of letter
            "1",                # graph is a superset of digit
            ["a", "1"],         # graph is a superset of alpha-num
            "-",                # graph is a superset of punct
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that graph data is a subset of (letter, digit, alpha-num, punct).
        """
        args = to_list(other)
        other_instance = TranslatedPattern.do_factory_create(*args)
        assert self.graph_node.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                ["a", "1", "#"],            # graph
                TranslatedGraphPattern      # (graph, graph) => graph
            ),
            (
                "abc.123",                  # mixed-word
                TranslatedMixedWordPattern  # (graph, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",                  # mixed-words
                TranslatedMixedWordsPattern # (graph, mixed-words) => mixed-words
            ),
            (
                "\xc8",                         # non-whitespace
                TranslatedNonWhitespacePattern # (graph, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",                      # non-whitespaces
                TranslatedNonWhitespacesPattern # (graph, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",                          # non-whitespace-group
                TranslatedNonWhitespacesGroupPattern    # (graph, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that graph type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.graph_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",                    # letter
                TranslatedGraphPattern  # (graph, letter) => graph
            ),
            (
                "1",                    # letter
                TranslatedGraphPattern  # (graph, letter) => graph
            ),
            (
                ["a", "1"],             # alpha-num
                TranslatedGraphPattern  # (graph, alpha-num) => graph
            ),
            (
                "-",                    # punct
                TranslatedGraphPattern  # (graph, punct) => graph
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that graph type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.graph_node.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc",                      # letters
                TranslatedMixedWordPattern  # (graph, letters) => mixed-word
            ),
            (
                "123",                      # digits
                TranslatedMixedWordPattern  # (graph, digits) => mixed-word
            ),
            (
                "1.1",                      # number
                TranslatedMixedWordPattern  # (graph, number) => mixed-word
            ),
            (
                "-1.1",                     # mixed-number
                TranslatedMixedWordPattern  # (graph, mixed-number) => mixed-word
            ),
            (
                "abc123",                   # word
                TranslatedMixedWordPattern  # (graph, word) => mixed-word
            ),
            (
                "a1 b1",                    # words
                TranslatedMixedWordsPattern # (graph, words) => mixed-words
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """

        if other.is_words():
            return TranslatedMixedWordsPattern(self.data, other.data)

        Verify that graph type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = TranslatedPattern.do_factory_create(*args)
        recommend_instance = self.graph_node.recommend(other)
        assert isinstance(recommend_instance, expected_class)
