"""
Unit tests for the `textfsmgen.engine.translate.NonWSSTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_non_wss_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_non_wss_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    make_translator,
    NonWSSTranslator,
    NonWSSGroupTranslator,
)

from tests.unit.engine.translate import to_list


class TestNonWSSTranslatorClass:
    """Test suite for NonWSSTranslator class."""

    def setup_method(self):
        """Create a baseline NonWSSTranslator instance for reuse."""
        self.translator = NonWSSTranslator("abc\xc8")

    @pytest.mark.parametrize(
        "other",
        [
            "abc\xc8",  # non-whitespaces are a subset of non-whitespaces
            "abc\xc8 xyz",  # non-whitespaces are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that non-whitespaces data is a subset of (non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "abc 123",  # non-whitespaces are not a subset of words
            "a.1 b.2",  # non-whitespaces are not a subset of mixed-words
            "-- ++ ==",  # non-whitespaces are not a subset of punct-group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that non-whitespaces data is not a subset of (puncts-group, words,
        mixed-words, non-whitespaces-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",  # non-whitespaces are a superset of letter
            "abc",  # non-whitespaces are a superset of letters
            "1",  # non-whitespaces are a superset of digit
            "123",  # non-whitespaces are a superset of digits
            "1.1",  # non-whitespaces are a superset of number
            "-1,1",  # non-whitespaces are a superset of mixed-number
            ["a", "1"],  # non-whitespaces are a superset of alpha-num
            ["a", "1", "#"],  # non-whitespaces are a superset of graph
            "-",  # non-whitespaces are a superset of punct
            "---++==",  # non-whitespaces are a superset of puncts
            "abc123",  # non-whitespaces are a superset of word
            "abc.123",  # non-whitespaces are a superset of mixed-word
            "\xc8",  # non-whitespaces are a superset of non-whitespace
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that non-whitespaces data is a superset of (letter(s)).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator,  # (non-whitespaces, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator,  # (non-whitespaces, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that non-whitespaces type correctly recommends a subset type
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
                NonWSSTranslator,  # (non-whitespaces, letter) => non-whitespaces
            ),
            (
                "abc",  # letters
                NonWSSTranslator,  # (non-whitespaces, letters) => non-whitespaces
            ),
            (
                "1",  # digit
                NonWSSTranslator,  # (non-whitespaces, digit) => non-whitespaces
            ),
            (
                "123",  # digits
                NonWSSTranslator,  # (non-whitespaces, digits) => non-whitespaces
            ),
            (
                "1.1",  # number
                NonWSSTranslator,  # (non-whitespaces, number) => non-whitespaces
            ),
            (
                "-1.1",  # mixed-number
                NonWSSTranslator,  # (non-whitespaces, mixed-number) => non-whitespaces
            ),
            (
                ["a", "1"],  # alpha-num
                NonWSSTranslator,  # (non-whitespaces, alpha-num) => non-whitespaces
            ),
            (
                ["a", "1", "#"],  # graph
                NonWSSTranslator,  # (non-whitespaces, graph) => non-whitespaces
            ),
            (
                "-",  # punct
                NonWSSTranslator,  # (non-whitespaces, punct) => non-whitespaces
            ),
            (
                "--++==",  # puncts
                NonWSSTranslator,  # (non-whitespaces, puncts) => non-whitespaces
            ),
            (
                "abc123",  # word
                NonWSSTranslator,  # (non-whitespaces, word) => non-whitespaces
            ),
            (
                "abc.123",  # mixed-word
                NonWSSTranslator,  # (non-whitespaces, mixed-word) => non-whitespaces
            ),
            (
                "\xc8",  # word
                NonWSSTranslator,  # (non-whitespaces, non-whitespace) => non-whitespaces
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that non-whitespaces type correctly recommends a superset type
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
                "a1 b1",  # words
                NonWSSGroupTranslator,  # (non-whitespaces, words) => non-whitespaces-group
            ),
            (
                "a.1 b.1",  # mixed-words
                NonWSSGroupTranslator,  # (non-whitespaces, mixed-words) => non-whitespaces-group
            ),
            (
                "-- ++ ==",  # punct-group
                NonWSSGroupTranslator,  # (non-whitespaces, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that non-whitespaces type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
