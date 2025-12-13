import pytest           # noqa

from textfsmgen.gp import TranslatedDigitPattern
from textfsmgen.gp import TranslatedDigitsPattern

from textfsmgen.gp import TranslatedLetterPattern
from textfsmgen.gp import TranslatedLettersPattern

from textfsmgen.gp import TranslatedAlphabetNumericPattern

from textfsmgen.gp import TranslatedWordPattern
from textfsmgen.gp import TranslatedWordsPattern

from textfsmgen.gp import TranslatedNonWhitespacePattern
from textfsmgen.gp import TranslatedNonWhitespacesPattern
from textfsmgen.gp import TranslatedNonWhitespacesGroupPattern


class TestTranslatedNonWhitespacePattern:
    """Test class for TranslatedNonWhitespacePattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('aa', ''),
            ('1', r'\S'),
            ('+', r'\S'),
            ('a', r'\S'),
        ]
    )
    def test_non_whitespace_pattern(self, data, expected_pattern):
        node = TranslatedNonWhitespacePattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('-', TranslatedLetterPattern('a'), r'\S'),
            ('.', TranslatedLettersPattern('ab'), r'\S+'),
            ('+', TranslatedDigitPattern('1'), r'\S'),
            ('*', TranslatedDigitsPattern('42'), r'\S+'),
            ('a', TranslatedAlphabetNumericPattern('4'), r'\S'),
            ('}', TranslatedWordPattern('4'), r'\S+'),
            ('=', TranslatedWordsPattern('4 5'), r'\S+( \S+)*'),
            ('@', TranslatedNonWhitespacesPattern('4'), r'\S+'),
            ('#', TranslatedNonWhitespacesGroupPattern('4'), r'\S+( \S+)*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedNonWhitespacePattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern
        assert recommended_pat == expected_pattern


class TestTranslatedNonWhitespacesPattern:
    """Test class for TranslatedNonWhitespacesPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('aa', r'\S+'),
            ('1', r'\S+'),
            ('+', r'\S+'),
            ('a', r'\S+'),
        ]
    )
    def test_non_whitespace_pattern(self, data, expected_pattern):
        node = TranslatedNonWhitespacesPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('-', TranslatedLetterPattern('a'), r'\S+'),
            ('.', TranslatedLettersPattern('ab'), r'\S+'),
            ('+', TranslatedDigitPattern('1'), r'\S+'),
            ('*', TranslatedDigitsPattern('42'), r'\S+'),
            ('a', TranslatedAlphabetNumericPattern('4'), r'\S+'),
            ('}', TranslatedWordPattern('4'), r'\S+'),
            ('=', TranslatedWordsPattern('4 5'), r'\S+( \S+)*'),
            ('@', TranslatedNonWhitespacesPattern('4'), r'\S+'),
            ('#', TranslatedNonWhitespacesGroupPattern('4'), r'\S+( \S+)*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedNonWhitespacesPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern
        assert recommended_pat == expected_pattern


class TestTranslatedNonWhitespacesGroupPattern:
    """Test class for TranslatedNonWhitespacesGroupPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('aa', r'\S+( \S+)*'),
            ('1', r'\S+( \S+)*'),
            ('+', r'\S+( \S+)*'),
            ('a', r'\S+( \S+)*'),
        ]
    )
    def test_non_whitespace_pattern(self, data, expected_pattern):
        node = TranslatedNonWhitespacesGroupPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('-', TranslatedLetterPattern('a'), r'\S+( \S+)*'),
            ('.', TranslatedLettersPattern('ab'), r'\S+( \S+)*'),
            ('+', TranslatedDigitPattern('1'), r'\S+( \S+)*'),
            ('*', TranslatedDigitsPattern('42'), r'\S+( \S+)*'),
            ('a', TranslatedAlphabetNumericPattern('4'), r'\S+( \S+)*'),
            ('}', TranslatedWordPattern('4'), r'\S+( \S+)*'),
            ('=', TranslatedWordsPattern('4 5'), r'\S+( \S+)*'),
            ('@', TranslatedNonWhitespacesPattern('4'), r'\S+( \S+)*'),
            ('#', TranslatedNonWhitespacesGroupPattern('4'), r'\S+( \S+)*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedNonWhitespacesGroupPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern
        assert recommended_pat == expected_pattern
