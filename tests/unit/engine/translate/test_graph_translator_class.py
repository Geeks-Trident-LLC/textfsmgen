"""
Unit tests for the `textfsmgen.gp.GraphTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_graph_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_graph_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    make_translator,
    GraphTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,
    NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator,
)

from tests.unit.engine.translate import to_list


class TestGraphTranslatorClass:
    """Test suite for GraphTranslator class."""

    def setup_method(self):
        """Create a baseline GraphTranslator instance for reuse."""
        self.translator = GraphTranslator("a", "1", "#")

    @pytest.mark.parametrize(
        "other",
        [
            ["a", "1", "#"],  # graph is a subset of graph
            "abc.123",  # graph is a subset of mixed word
            "a.1 b.2",  # graph is a subset of mixed words
            "\xc8",  # graph is a subset of non-whitespace
            "abc\xc8",  # graph is a subset of non-whitespaces
            "abc\xc8 xyz",  # graph is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that graph data is a subset of (mixed-word(s), non-whitespace(s)(-group))
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "123",  # graph is not a subset of digits
            "1.1",  # graph is not a subset of number
            "-1.1",  # graph is not a subset of mixed-number
            "++--",  # graph is not a subset of punctuation(s)
            "++ -- ==",  # graph is not a subset of punctuation group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that graph data is not a subset of (digits, number,
        mixed-number, punctuation(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",  # graph is a superset of letter
            "1",  # graph is a superset of digit
            ["a", "1"],  # graph is a superset of alpha-num
            "-",  # graph is a superset of punct
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that graph data is a subset of (letter, digit, alpha-num, punct).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                ["a", "1", "#"],  # graph
                GraphTranslator,  # (graph, graph) => graph
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator,  # (graph, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator,  # (graph, mixed-words) => mixed-words
            ),
            (
                "\xc8",  # non-whitespace
                NonWSTranslator,  # (graph, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator,  # (graph, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator,  # (graph, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that graph type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",  # letter
                GraphTranslator,  # (graph, letter) => graph
            ),
            (
                "1",  # letter
                GraphTranslator,  # (graph, letter) => graph
            ),
            (
                ["a", "1"],  # alpha-num
                GraphTranslator,  # (graph, alpha-num) => graph
            ),
            (
                "-",  # punct
                GraphTranslator,  # (graph, punct) => graph
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that graph type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc",  # letters
                MixedWordTranslator,  # (graph, letters) => mixed-word
            ),
            (
                "123",  # digits
                MixedWordTranslator,  # (graph, digits) => mixed-word
            ),
            (
                "1.1",  # number
                MixedWordTranslator,  # (graph, number) => mixed-word
            ),
            (
                "-1.1",  # mixed-number
                MixedWordTranslator,  # (graph, mixed-number) => mixed-word
            ),
            (
                "abc123",  # word
                MixedWordTranslator,  # (graph, word) => mixed-word
            ),
            (
                "a1 b1",  # words
                MixedWordsTranslator,  # (graph, words) => mixed-words
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that graph type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
