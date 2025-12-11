import pytest           # noqa

from textfsmgenerator.gp import TranslatedDigitPattern
from textfsmgenerator.gp import TranslatedDigitsPattern

from textfsmgenerator.gp import TranslatedLetterPattern
from textfsmgenerator.gp import TranslatedLettersPattern

from textfsmgenerator.gp import TranslatedAlphabetNumericPattern

from textfsmgenerator.gp import TranslatedWordPattern
from textfsmgenerator.gp import TranslatedMixedWordPattern
from textfsmgenerator.gp import TranslatedMixedWordsPattern


class TestTranslatedMixedWordPattern:
    """Test class for TranslatedMixedWordPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('ab xy', ''),
            ('1', "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('abc', "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('192.168.0.1', "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('a::b', "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
        ]
    )
    def test_mixed_word_pattern(self, data, expected_pattern):
        node = TranslatedMixedWordPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a', TranslatedLetterPattern('a'), "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('a', TranslatedLettersPattern('ab'), "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('a', TranslatedDigitPattern('1'), "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('a', TranslatedDigitsPattern('4'), "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('a', TranslatedAlphabetNumericPattern('4'), "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
            ('a', TranslatedWordPattern('4'), "[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*"),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedMixedWordPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedMixedWordsPattern:
    """Test class for TranslatedMixedWordsPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('ab xy', '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)+'),
            ('1', '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('abc', '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('192.168.0.1', '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('a::b', '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
        ]
    )
    def test_mixed_words_pattern(self, data, expected_pattern):
        node = TranslatedMixedWordsPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a b', TranslatedLetterPattern('a'),
             '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('a b', TranslatedLettersPattern('ab'),
             '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('a b', TranslatedDigitPattern('1'),
             '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('a b', TranslatedDigitsPattern('4'),
             '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('a b', TranslatedAlphabetNumericPattern('4'),
             '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
            ('a b', TranslatedWordPattern('4'),
             '[\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*( [\\x21-\\x7e]*[a-zA-Z0-9][\\x21-\\x7e]*)*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedMixedWordsPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern
