"""
Unit tests for the `textfsmgen.engine.translate.PunctsTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_puncts_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_puncts_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    PatternTranslator,
# DigitTranslator,
# DigitsTranslator,
# NumberTranslator,
# MixedNumberTranslator,
# LetterTranslator,
# LettersTranslator,
# AlnumTranslator,
# PunctTranslator,
    PunctsTranslator,
    PunctsGroupTranslator,
# GraphTranslator,
# WordTranslator,
# WordsTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,
# NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestPunctsTranslatorClass:
    """Test suite for PunctsTranslator class."""

    def setup_method(self):
        """Create a baseline PunctsTranslator instance for reuse."""
        self.translator = PunctsTranslator("--")

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
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # puncts are not a subset of digit
            "123",              # puncts are not a subset of digits
            "1.1",              # puncts are not a subset of number
            "-1.1",             # puncts are not a subset of mixed-number
            "a",                # puncts are not a subset of letter
            "abc",              # puncts are not a subset of letters
            "a1 b1",            # puncts are not a subset of words

        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that punctuations data is not a subset of (digits, number,
        mixed-number, letter(s), word(s))
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is False

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
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "--++==",  # puncts
                PunctsTranslator # (puncts, puncts) => puncts
            ),
            (
                "-- ++ ==",  # punct-group
                PunctsGroupTranslator # (puncts, punct-group) => punct-group
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator  # (puncts, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (puncts, mixed-words) => mixed-words
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (puncts, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (puncts, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that punctuations type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-",  # punct
                PunctsTranslator # (puncts, punct) => punct
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that punctuations type correctly recommends a superset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",  # letter
                NonWSSTranslator # (puncts, letter) => non-whitespaces
            ),
            (
                "1",  # digit
                NonWSSTranslator # (puncts, digit) => non-whitespaces
            ),
            (
                    ["a", "1"],  # alpha-num
                    NonWSSTranslator # (puncts, alpha-num) => non-whitespaces
            ),
            (
                    ["a", "1", "#"],  # graph
                    NonWSSTranslator # (puncts, graph) => non-whitespaces
            ),
            (
                "abc",  # letters
                NonWSSTranslator # (puncts, letters) => non-whitespaces
            ),
            (
                "123",  # digits
                NonWSSTranslator # (puncts, digits) => non-whitespaces
            ),
            (
                "1.1",  # number
                NonWSSTranslator # (puncts, number) => non-whitespaces
            ),
            (
                "-1.1",  # mixed-number
                NonWSSTranslator # (puncts, mixed-number) => non-whitespaces
            ),
            # (
            #     "abc123",  # word
            #     NonWSSTranslator # (puncts, word) => non-whitespaces
            # ),
            (
                "\xc8",  # non-whitespace
                NonWSSTranslator # (puncts, non-whitespace) => non-whitespaces
            ),
            (
                "a1 b1",  # words
                NonWSSGroupTranslator    # (puncts, words) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that punctuations type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
