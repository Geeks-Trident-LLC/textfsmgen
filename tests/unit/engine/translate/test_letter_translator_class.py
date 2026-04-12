"""
Unit tests for the `textfsmgen.engine.translate.LetterTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_letter_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_letter_translator_class.py
"""

import pytest   # noqa

from textfsmgen.engine.translate import (
    make_translator,

    LetterTranslator,
    LettersTranslator,
    AlnumTranslator,

    GraphTranslator,
    WordTranslator,
    WordsTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,
    NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestLetterTranslatorClass:
    """Test suite for LetterTranslator class."""

    def setup_method(self):
        """Create a baseline LetterTranslator instance for reuse."""
        self.translator = LetterTranslator("a" "b", "c")

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # a letter is a subset of letter
            "ab",               # a letter is a subset of letters
            ["a", "1"],         # a letter is a subset of alphabet numeric
            ["a", "1", "#"],    # a letter is a subset of graph
            "abc123",           # a letter is a subset of word
            "a1 b12",           # a letter is a subset of words
            "abc.123",          # a letter is a subset of mixed word
            "a.1 b.2",          # a letter is a subset of mixed words
            "\xc8",             # a letter is a subset of non-whitespace
            "abc\xc8",          # a letter is a subset of non-whitespaces
            "abc\xc8 xyz",      # a letter is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that a letter data is a subset of (letter(s), alpha-num,
        graph, word(s), mixed-word(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # a letter is not a subset of digit
            "123",              # a letter is not a subset of digits
            "1.1",              # a letter is not a subset of number
            "-1.1",             # a letter is not a subset of mixed-number
            "++--",             # a letter is not a subset of punctuation(s)
            "++ -- ==",         # a letter is not a subset of punctuation group
        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that a letter data is not a subset of (letter(s), number,
        mixed-number, punctuation(s), non-whitespace(s), non-whitespace-group)
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # a letter is not a superset of digit
            "123",              # a letter is not a superset of digits
            "1.1",              # a letter is not a superset of number
            "abc\xc8 xyz",      # a letter is not a superset of non-whitespace group
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that a letter data is correctly identified as not belonging
        to any broader translated category.
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is False

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "a",  # letter
                LetterTranslator     # (letter, letter) => letter
            ),
            (
                "abc",  # letters
                LettersTranslator    # (letter, letters) => letters
            ),
            (
                    ["a", "1"],  # alpha-num
                    AlnumTranslator    # (letter, alpha-num) => alpha-num
            ),
            (
                    ["a", "1", "#"],  # graph
                    GraphTranslator  # (letter, graph) => graph
            ),
            (
                "abc123",  # a word
                WordTranslator   # (letter, word) => word
            ),
            (
                "a1 a12",  # words
                WordsTranslator  # (letter, words) => words
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator  # (letter, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (letter, mixed-words) => mixed-words
            ),
            (
                "\xc8",  # non-whitespace
                NonWSTranslator  # (letter, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (letter, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (letter, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that a letter type correctly recommends a subset type
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
                "1",  # digit
                AlnumTranslator    # (letter, digit) => alpha-num
            ),
            (
                "123",  # digits
                WordTranslator   # (letter, digits) => digits
            ),
            (
                "1.1",  # number
                MixedWordTranslator  # (letter, number) => mixed-word
            ),
            (
                "-1.1",  # mixed-number
                MixedWordTranslator  # (letter, mixed-number) => mixed-word
            ),
            (
                "+",  # punctuation
                GraphTranslator      # (letter, punct) => punct
            ),
            (
                "++",  # punctuations
                NonWSSTranslator # (letter, puncts) => non-whitespaces
            ),
            (
                "++ -- ==",  # punctuation-group
                NonWSSGroupTranslator    # (letter, punct-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that a letter type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
