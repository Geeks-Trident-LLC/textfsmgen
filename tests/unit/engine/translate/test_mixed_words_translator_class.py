"""
Unit tests for the `textfsmgen.engine.translate.MixedWordsTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/translate/test_mixed_words_translator_class.py
    or
    $ python -m pytest tests/unit/engine/translate/test_mixed_words_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import (
    make_translator,

    MixedWordsTranslator,

    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestMixedWordsTranslatorClass:
    """Test suite for MixedWordsTranslator class."""

    def setup_method(self):
        """Create a baseline MixedWordsTranslator instance for reuse."""
        self.translator = MixedWordsTranslator("a.1 b.2")

    @pytest.mark.parametrize(
        "other",
        [
            "a.1 b.2",          # mixed-words are a subset of mixed-words
            "abc\xc8 xyz",      # mixed-words are a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that mixed-words data is a subset of (mixed-words, non-whitespaces-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # mixed-words are not a subset of punct
            "--++==",           # mixed-words are not a subset of puncts
            "-- ++ ==",         # mixed-words are not a subset of punct-group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that mixed-words data is not a subset of (punct(s)(-group), number,
        mixed-number, graph)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # mixed-words are a superset of letter
            "abc",              # mixed-words are a superset of letters
            "1",                # mixed-words are a superset of digit
            "123",              # mixed-words are a superset of digits
            "1.1",              # mixed-words are a superset of number
            "-1.1",             # mixed-words are a superset of mixed-number
            ["a", "1"],         # mixed-words are a superset of alpha-num
            "abc123",           # mixed-words are a superset of word
            "a1 b2",            # mixed-words are a superset of words
            "a.1",              # mixed-words are a superset of mixed-word
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that mixed-words data is a superset of (letter(s), digit(s),
        number, mixed-number, alpha-num, word).
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is True

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (mixed-words, mixed-words) => mixed-words
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (mixed-words, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that mixed-words type correctly recommends a subset type
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
                MixedWordsTranslator # (mixed-words, letter) => mixed-words
            ),
            (
                "abc",  # letters
                MixedWordsTranslator # (mixed-words, letters) => mixed-words
            ),
            (
                "1",  # digit
                MixedWordsTranslator # (mixed-words, digit) => mixed-words
            ),
            (
                "123",  # digits
                MixedWordsTranslator # (mixed-words, digits) => mixed-words
            ),
            (
                "1.1",  # number
                MixedWordsTranslator # (mixed-words, number) => mixed-words
            ),
            (
                "-1.1",  # mixed-number
                MixedWordsTranslator # (mixed-words, mixed-number) => mixed-word
            ),
            (
                    ["a", "1"],  # alpha-num
                    MixedWordsTranslator # (mixed-words, alpha-num) => mixed-word
            ),
            (
                "abc123",  # word
                MixedWordsTranslator # (mixed-words, word) => mixed-word
            ),
            (
                "a1 b1",  # words
                MixedWordsTranslator # (mixed-words, words) => mixed-words
            ),
            (
                "abc.123",  # mixed-word
                MixedWordsTranslator # (mixed-words, mixed-word) => mixed-words
            ),
        ],
    )
    def test_recommend_method_case_superset(self, data, expected_class):
        """
        Verify that mixed-words type correctly recommends a superset type
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
                    ["a", "1", "#"],  # graph
                    NonWSSGroupTranslator    # (mixed-words, graph) => non-whitespaces-group
            ),
            (
                "\xc8",  # non-whitespace
                NonWSSGroupTranslator    # (mixed-words, non-whitespace) => non-whitespaces-group
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSGroupTranslator    # (mixed-words, non-whitespaces) => non-whitespaces-group
            ),
            (
                "-",  # punct
                NonWSSGroupTranslator    # (mixed-words, non-whitespace) => non-whitespaces-group
            ),
            (
                "--++==",  # puncts
                NonWSSGroupTranslator    # (mixed-words, puncts) => non-whitespaces-group
            ),
            (
                "-- ++ ==",  # punct-group
                NonWSSGroupTranslator    # (mixed-words, punct-group) => non-whitespaces-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that mixed-words type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
