"""
Unit tests for the `textfsmgen.engine.translate.PunctTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_punct_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_punct_translator_class.py
"""

import pytest   # noqa

from textfsmgen.engine.translate import (
    make_translator,

    PunctTranslator,
    PunctsTranslator,
    PunctsGroupTranslator,
    GraphTranslator,

    MixedWordTranslator,
    MixedWordsTranslator,
    NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator
)

to_list = lambda arg: arg if isinstance(arg, (list, tuple)) else [arg]


class TestPunctTranslatorClass:
    """Test suite for PunctTranslator class."""

    def setup_method(self):
        """Create a baseline PunctTranslator instance for reuse."""
        self.translator = PunctTranslator("-")

    @pytest.mark.parametrize(
        "other",
        [
            "-",                # punct is a subset of punct
            ["a", "1", "#"],    # punct is a subset of graph
            "==",               # punct is a subset of puncts
            "-- ++ =="          # punct is a subset of punct-group
            "abc.123",          # punct is a subset of mixed-word
            "a.1 b.2",          # punct is a subset of mixed-words
            "\xc8",             # punct is a subset of non-whitespace
            "abc\xc8",          # punct is a subset of non-whitespaces
            "abc\xc8 xyz",      # punct is a subset of non-whitespace group
        ],
    )
    def test_is_subset_of(self, other):
        """
        Verify that punctuation data is a subset of (punct(s)(-group),
        graph, mixed-word(s), non-whitespace(s)(-group))
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is True

    @pytest.mark.parametrize(
        "other",
        [
            "1",                # punct is not a subset of digit
            "123",              # punct is not a subset of digits
            "1.1",              # punct is not a subset of number
            "-1.1",             # punct is not a subset of mixed-number
            "a",                # punct is not a subset of letter
            "abc",              # punct is not a subset of letters
            "a1 b1",            # punct is not a subset of words

        ],
    )
    def test_is_not_subset_of(self, other):
        """
        Verify that punctuation data is not a subset of (digits, number,
        mixed-number, letter(s), word(s))
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_subset_of(other_instance) is False

    @pytest.mark.parametrize(
        "other",
        [
            "a",                # punct is not a superset of letter
            "1",                # punct is not a superset of digit
            ["a", "1"],         # punct is not a superset of alpha-num
        ],
    )
    def test_is_superset_of(self, other):
        """
        Verify that punctuation data does not have any superset.
        """
        args = to_list(other)
        other_instance = make_translator(*args)
        assert self.translator.is_superset_of(other_instance) is False

    @pytest.mark.parametrize(
        "data, expected_class",
        [
            (
                "-",  # punct
                PunctTranslator  # (punct, punct) => punct
            ),
            (
                "--++==",  # puncts
                PunctsTranslator # (punct, puncts) => puncts
            ),
            (
                "-- ++ ==",  # punct-group
                PunctsGroupTranslator # (punct, punct-group) => punct-group
            ),
            (
                    ["a", "1", "#"],  # graph
                    GraphTranslator      # (punct, graph) => graph
            ),
            (
                "abc.123",  # mixed-word
                MixedWordTranslator  # (punct, mixed-word) => mixed-word
            ),
            (
                "a.1 b.1",  # mixed-words
                MixedWordsTranslator # (punct, mixed-words) => mixed-words
            ),
            (
                "\xc8",  # non-whitespace
                NonWSTranslator # (punct, non-whitespace) => non-whitespace
            ),
            (
                "abc\xc8",  # non-whitespaces
                NonWSSTranslator # (punct, non-whitespaces) => non-whitespaces
            ),
            (
                "abc\xc8 xyz",  # non-whitespace-group
                NonWSSGroupTranslator    # (punct, non-whitespace-group) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_subset(self, data, expected_class):
        """
        Verify that punctuation type correctly recommends a subset type
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
                GraphTranslator  # (punct, letter) => graph
            ),
            (
                "1",  # digit
                GraphTranslator  # (punct, digit) => graph
            ),
            (
                    ["a", "1"],  # alpha-num
                    GraphTranslator  # (punct, alpha-num) => graph
            ),

            (
                "abc",  # letters
                NonWSSTranslator # (punct, letters) => non-whitespaces
            ),
            (
                "123",  # digits
                NonWSSTranslator # (punct, digits) => non-whitespaces
            ),
            (
                "1.1",  # number
                NonWSSTranslator # (punct, number) => non-whitespaces
            ),
            (
                "-1.1",  # mixed-number
                NonWSSTranslator # (punct, mixed-number) => non-whitespaces
            ),
            # (
            #     "abc123",  # word
            #     NonWSSTranslator # (punct, word) => non-whitespaces
            # ),
            (
                "a1 b1",  # words
                NonWSSGroupTranslator    # (punct, words) => non-whitespace-group
            ),
        ],
    )
    def test_recommend_method_case_aggregating(self, data, expected_class):
        """
        Verify that punctuation type correctly recommends a subset type
        when combined with compatible data.
        """
        args = to_list(data)
        other = make_translator(*args)
        recommend_instance = self.translator.recommend(other)
        assert isinstance(recommend_instance, expected_class)
