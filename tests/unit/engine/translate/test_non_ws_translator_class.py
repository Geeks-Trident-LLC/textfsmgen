"""
Unit tests for the `textfsmgen.engine.translate.NonWSTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_non_ws_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_non_ws_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    make_translator,
    NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator,
)

from tests.unit.engine.translate import to_list


class TestNonWSTranslatorClass:
    """Test suite for NonWSTranslator class."""

    def setup_method(self):
        """Create a baseline NonWSTranslator instance for reuse."""
        self.translator = NonWSTranslator("\xc8")

    @pytest.mark.parametrize(
        "other",
        [
            "\xc8",  # non-whitespace is a subset of non-whitespace
            "abc\xc8",  # non-whitespace is a subset of non-whitespaces
            "abc\xc8 xyz",  # non-whitespace is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that non-whitespace data is a subset of (non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "--++==",  # non-whitespace is not a subset of puncts
            "-- ++ ==",  # non-whitespace is not a subset of punct-group
            "1.1",  # non-whitespace is not a subset of number
            "-1.1",  # non-whitespace is not a subset of mixed-number
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that non-whitespace data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",  # non-whitespace is a superset of letter
            "1",  # non-whitespace is a superset of digit
            ["a", "1"],  # non-whitespace is a superset of alpha-num
            "-",  # non-whitespace is a superset of digit
            ["a", "1", "#"],  # non-whitespace is a superset of graph
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that non-whitespace data is a superset of (letter(s)).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "\xc8",  # non-whitespace
                NonWSTranslator,  # (non-whitespace, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator,  # (non-whitespace, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator,  # (non-whitespace, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that non-whitespace type correctly recommends a subset type
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
                NonWSTranslator,  # (non-whitespace, letter) => non-whitespace
            ),
            (
                "1",  # digit
                NonWSTranslator,  # (non-whitespace, digit) => non-whitespace
            ),
            (
                ["a", "1"],  # alpha-num
                NonWSTranslator,  # (non-whitespace, alpha-num) => non-whitespace
            ),
            (
                "-",  # punct
                NonWSTranslator,  # (non-whitespace, punct) => non-whitespace
            ),
            (
                ["a", "1", "#"],  # graph
                NonWSTranslator,  # (non-whitespace, graph) => non-whitespace
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that non-whitespace type correctly recommends a superset type
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
                NonWSSTranslator,  # (non-whitespace, letters) => non-whitespaces
            ),
            (
                "123",  # digits
                NonWSSTranslator,  # (non-whitespace, digit) => non-whitespaces
            ),
            (
                "--++==",  # puncts
                NonWSSTranslator,  # (non-whitespace, puncts) => non-whitespaces
            ),
            (
                "1.1",  # number
                NonWSSTranslator,  # (non-whitespace, number) => non-whitespaces
            ),
            (
                "-1.1",  # mixed-number
                NonWSSTranslator,  # (non-whitespace, mixed-number) => non-whitespaces
            ),
            (
                "abc123",  # word
                NonWSSTranslator,  # (non-whitespace, word) => non-whitespaces
            ),
            (
                "abc.123",  # mixed-word
                NonWSSTranslator,  # (non-whitespace, mixed-word) => non-whitespaces
            ),
            (
                "a1 b1",  # words
                NonWSSGroupTranslator,  # (non-whitespace, words) => non-whitespaces-group
            ),
            (
                "a.1 b.1",  # mixed-words
                NonWSSGroupTranslator,  # (non-whitespace, mixed-words) => non-whitespaces-group
            ),
            (
                "-- ++ ==",  # punct-group
                NonWSSGroupTranslator,  # (non-whitespace, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that non-whitespace type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
