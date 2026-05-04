"""
Unit tests for the `textfsmgen.engine.translate.PunctsGroupTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_puncts_group_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_puncts_group_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    make_translator,
    PunctsGroupTranslator,
    MixedWordsTranslator,
    NonWSSGroupTranslator,
)

from tests.unit.engine.translate import to_list


class TestPunctsGroupTranslatorClass:
    """Test suite for PunctsGroupTranslator class."""

    def setup_method(self):
        """Create a baseline PunctsGroupTranslator instance for reuse."""
        self.translator = PunctsGroupTranslator("-- ++ ==")

    @pytest.mark.parametrize(
        "other",
        [
            "-- ++ =="  # punct-group is a subset of punct-group
            "a.1 b.2",  # punct-group is a subset of mixed-words
            "abc\xc8 xyz",  # punct-group is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that punctuation-group data is a subset of (punct-group,
        mixed-words, non-whitespaces-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",  # punct-group is not a subset of digit
            "123",  # punct-group is not a subset of digits
            "1.1",  # punct-group is not a subset of number
            "-1.1",  # punct-group is not a subset of mixed-number
            "a",  # punct-group is not a subset of letter
            "abc",  # punct-group is not a subset of letters
            "abc123",  # punct-group is not a subset of word
            "a1 b1",  # punct-group is not a subset of words
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that punctuation-group data is not a subset of (digits, number,
        mixed-number, letter(s), word(s))
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            ".",  # punct-group is a superset of punct
            "++==--",  # punct-group is a superset of puncts
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that punctuation-group data is a superset of (punct(s)).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-- ++ ==",  # punct-group
                PunctsGroupTranslator,  # (punct-group, punct-group) => punct-group
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator,  # (punct-group, mixed-words) => mixed-words
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator,  # (punct-group, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that punctuation-group type correctly recommends a subset type
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
                "-",  # punct
                PunctsGroupTranslator,  # (punct-group, punct) => punct-group
            ),
            (
                "--++==",  # puncts
                PunctsGroupTranslator,  # (punct-group, puncts) => punct-group
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that punctuation-group type correctly recommends a superset type
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
                NonWSSGroupTranslator,  # (punct-group, letter) => non-whitespace-group
            ),
            (
                "1",  # digit
                NonWSSGroupTranslator,  # (punct-group, digit) => non-whitespace-group
            ),
            (
                ["a", "1"],  # alpha-num
                NonWSSGroupTranslator,  # (punct-group, alpha-num) => non-whitespace-group
            ),
            (
                ["a", "1", "#"],  # graph
                NonWSSGroupTranslator,  # (punct-group, graph) => non-whitespace-group
            ),
            (
                "abc",  # letters
                NonWSSGroupTranslator,  # (punct-group, letters) => non-whitespace-group
            ),
            (
                "123",  # digits
                NonWSSGroupTranslator,  # (punct-group, digits) => non-whitespace-group
            ),
            (
                "1.1",  # number
                NonWSSGroupTranslator,  # (punct-group, number) => non-whitespace-group
            ),
            (
                "-1.1",  # mixed-number
                NonWSSGroupTranslator,  # (punct-group, mixed-number) => non-whitespace-group
            ),
            (
                "abc123",  # word
                NonWSSGroupTranslator,  # (punct-group, word) => non-whitespace-group
            ),
            (
                "a1 b1",  # words
                NonWSSGroupTranslator,  # (punct-group, words) => non-whitespace-group
            ),
            (
                "\xc8",  # non-whitespace
                NonWSSGroupTranslator,  # (punct-group, non-whitespace) => non-whitespace-group
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSGroupTranslator,  # (punct-group, non-whitespaces) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that punctuation-group type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
