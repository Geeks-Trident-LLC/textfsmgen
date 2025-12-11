import pytest           # noqa

from textfsmgenerator.gp import TranslatedDigitPattern
from textfsmgenerator.gp import TranslatedDigitsPattern

from textfsmgenerator.gp import TranslatedNumberPattern
from textfsmgenerator.gp import TranslatedMixedNumberPattern

from textfsmgenerator.gp import TranslatedLetterPattern
from textfsmgenerator.gp import TranslatedLettersPattern

from genericlib.gp import TranslatedAlphabetNumericPattern


class TestTranslatedDigitPattern:
    """Test class for TranslatedDigitPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('5', r'\d'),
            ('', ''),
            ('123', ''),
        ]
    )
    def test_digit_pattern(self, data, expected_pattern):
        node = TranslatedDigitPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('5', TranslatedDigitPattern('4'), r'\d'),
            ('5', TranslatedDigitsPattern('44'), r'\d+'),
            ('5', TranslatedNumberPattern('4.4'), r'\d*[.]?\d+'),
            ('5', TranslatedMixedNumberPattern('4.4'),  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedDigitPattern(data)

        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedDigitsPattern:
    """Test class for TranslatedDigitsPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('5', r'\d+'),
            ('123', r'\d+'),
        ]
    )
    def test_digits_pattern(self, data, expected_pattern):
        node = TranslatedDigitsPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('5', TranslatedDigitPattern('4'), r'\d+'),
            ('5', TranslatedDigitsPattern('44'), r'\d+'),
            ('5', TranslatedNumberPattern('4.4'), r'\d*[.]?\d+'),
            ('5', TranslatedMixedNumberPattern('4.4'),  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedDigitsPattern(data)

        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedNumberPattern:
    """Test class for TranslatedNumberPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('5', r'\d*[.]?\d+'),
            ('.5', r'\d*[.]?\d+'),
            ('0.5', r'\d*[.]?\d+'),
            ('-0.5', ''),
        ]
    )
    def test_number_pattern(self, data, expected_pattern):
        node = TranslatedNumberPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('5.1', TranslatedDigitPattern('4'), r'\d*[.]?\d+'),
            ('5.1', TranslatedDigitsPattern('44'), r'\d*[.]?\d+'),
            ('5.1', TranslatedNumberPattern('4.4'), r'\d*[.]?\d+'),
            ('5.1', TranslatedMixedNumberPattern('4.4'),  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedNumberPattern(data)

        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedMixedNumberPattern:
    """Test class for TranslatedNumberPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('5',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('.5',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('0.5',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('-0.5',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('+0.5',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('(0.5)',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
        ]
    )
    def test_mixed_number_pattern(self, data, expected_pattern):
        node = TranslatedMixedNumberPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('+5.1', TranslatedDigitPattern('4'),  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('-5.1', TranslatedDigitsPattern('44'),  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('(5.1)', TranslatedNumberPattern('4.4'),  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedMixedNumberPattern(data)

        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedLetterPattern:
    """Test class for TranslatedLetterPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('ab', ''),
            ('b', '[a-zA-Z]'),
        ]
    )
    def test_letter_pattern(self, data, expected_pattern):
        node = TranslatedLetterPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a', TranslatedLetterPattern('a'), '[a-zA-Z]'),
            # ('a', TranslatedDigitPattern('4'), ''),
            # ('a', TranslatedDigitsPattern('4'), ''),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedLetterPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedLettersPattern:
    """Test class for TranslatedLettersPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('ab', '[a-zA-Z]+'),
            ('b', '[a-zA-Z]+'),
        ]
    )
    def test_letters_pattern(self, data, expected_pattern):
        node = TranslatedLettersPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a', TranslatedLetterPattern('a'), '[a-zA-Z]+'),
            ('a', TranslatedLettersPattern('ac'), '[a-zA-Z]+'),
            # ('a', TranslatedDigitsPattern('4'), ''),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedLettersPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern


class TestTranslatedAlphabetNumericPattern:
    """Test class for TranslatedAlphabetNumericPattern."""

    @pytest.mark.parametrize(
        "data,expected_pattern",
        [
            ('', ''),
            ('1', '[a-zA-Z0-9]'),
            ('b', '[a-zA-Z0-9]'),
        ]
    )
    def test_alphabet_numeric_pattern(self, data, expected_pattern):
        node = TranslatedAlphabetNumericPattern(data)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "data,other,expected_pattern",
        [
            ('a', TranslatedLetterPattern('a'), '[a-zA-Z0-9]'),
            ('a', TranslatedAlphabetNumericPattern('1'), '[a-zA-Z0-9]'),
            # ('a', TranslatedDigitsPattern('4'), ''),
        ]
    )
    def test_recommend_pattern(self, data, other, expected_pattern):
        node = TranslatedAlphabetNumericPattern(data)
        recommended_pat_obj = node.recommend(other)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern
