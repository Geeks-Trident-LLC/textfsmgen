import pytest           # noqa

from textfsmgen.gp import TranslatedDigitPattern
from textfsmgen.gp import TranslatedDigitsPattern

from textfsmgen.gp import TranslatedLetterPattern
from textfsmgen.gp import TranslatedLettersPattern

from textfsmgen.gp import TranslatedAlphabetNumericPattern

from textfsmgen.gp import TranslatedWordPattern
from textfsmgen.gp import TranslatedWordsPattern


class TestTranslatedWordPattern:
    """Test class for TranslatedWordPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('a1', "[a-zA-Z][a-zA-Z0-9]*"),
            ('ab', "[a-zA-Z][a-zA-Z0-9]*"),
        ]
    )
    def test_word_pattern(self, data, expected_pattern):
        node = TranslatedWordPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a', TranslatedLetterPattern('a'), "[a-zA-Z][a-zA-Z0-9]*"),
            ('a', TranslatedLettersPattern('ab'), "[a-zA-Z][a-zA-Z0-9]*"),
            ('a', TranslatedDigitPattern('1'), '\\S+'),
            ('a', TranslatedDigitsPattern('4'), '\\S+'),
            ('a', TranslatedAlphabetNumericPattern('a'), r"\S+"),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedWordPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedWordsPattern:
    """Test class for TranslatedWordsPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('ab xy', "[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+"),
            ('a1 x2', "[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+"),
            ('ab xy', "[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+"),
        ]
    )
    def test_words_pattern(self, data, expected_pattern):
        node = TranslatedWordsPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a b', TranslatedLetterPattern('a'), "[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*"),
            ('a b', TranslatedLettersPattern('ab'), "[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*"),
            ('a b', TranslatedDigitPattern('1'), "\\S+( \\S+)*"),
            ('a b', TranslatedDigitsPattern('4'), "\\S+( \\S+)*"),
            ('a b', TranslatedAlphabetNumericPattern('a'), r"\S+( \S+)*"),
            ('a b', TranslatedWordPattern('a4'), "[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*"),
            ('a b', TranslatedWordsPattern('ab  xy'), "[a-zA-Z][a-zA-Z0-9]*( +[a-zA-Z][a-zA-Z0-9]*)+"),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedWordsPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern
