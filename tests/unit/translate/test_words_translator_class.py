"""
Unit tests for the `textfsmgen.engine.translate.WordsTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_words_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_words_translator_class.py
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
# PunctsTranslator,
# PunctsGroupTranslator,
# GraphTranslator,
# WordTranslator,
    WordsTranslator,
# MixedWordTranslator,
    MixedWordsTranslator,
# NonWSTranslator,
# NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestWordsTranslatorClass:
    """Test suite for WordsTranslator class."""

    def setup_method(self):
        """Create a baseline WordsTranslator instance for reuse."""
        self.translator = WordsTranslator("abc123")

    @pytest.mark.parametrize(
        "other",
        [
            "a1 b2"             # words are a subset of words
            "a.1 b.2",          # words are a subset of mixed-words
            "abc\xc8 xyz",      # words are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that words data is a subset of (word(s), mixed-word(s), non-whitespaces(-group))
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # words are not a subset of punct
            "--++==",           # words are not a subset of puncts
            "-- ++ ==",         # words are not a subset of punct-group
            "1.1",              # words are not a subset of number
            "-1.1",             # words are not a subset of mixed-number
            ["a", "1", "#"],    # words are not a subset of graph
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that words data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # words are a superset of letter
            "abc",              # words are a superset of letters
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that words data is a superset of (letter(s), word).
        """
        args = to_list(other)
        other_instance = PatternTranslator.do_factory_create(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a1 b2",  # words
                WordsTranslator  # (words, words) => words
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (words, mixed-words) => mixed-words
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (words, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that words type correctly recommends a subset type
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
                WordsTranslator  # (words, letter) => words
            ),
            (
                "abc",  # letters
                WordsTranslator  # (words, letters) => words
            ),
            # (
            #     "abc123",               # word
            #     WordsTranslator  # (words, word) => words
            # ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that words type correctly recommends a superset type
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
                    ["a", "1"],  # alpha-num
                    NonWSSGroupTranslator    # (words, alpha-num) => non-whitespaces-group
            ),
            (
                    ["a", "1", "#"],  # graph
                    NonWSSGroupTranslator    # (words, graph) => non-whitespaces-group
            ),
            (
                "1",  # digit
                NonWSSGroupTranslator    # (words, digit) => non-whitespaces-group
            ),
            (
                "123",  # digits
                NonWSSGroupTranslator    # (words, digits) => non-whitespaces-group
            ),
            (
                "1.23",  # number
                NonWSSGroupTranslator    # (words, number) => non-whitespaces-group
            ),
            (
                "-1.1",  # mixed-number
                NonWSSGroupTranslator    # (words, mixed-number) => non-whitespaces-group
            ),
            (
                "\xc8",  # non-whitespace
                NonWSSGroupTranslator    # (words, non-whitespace) => non-whitespaces-group
            ),
            (
                "-",  # punct
                NonWSSGroupTranslator    # (words, non-whitespace) => non-whitespaces-group
            ),
            (
                "--++==",  # puncts
                NonWSSGroupTranslator    # (words, puncts) => non-whitespaces-group
            ),
            (
                "-- ++ ==",  # punct-group
                NonWSSGroupTranslator    # (words, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that words type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = PatternTranslator.do_factory_create(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
