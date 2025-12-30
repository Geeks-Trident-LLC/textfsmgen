import pytest           # noqa

from textfsmgen.gp import TranslatedPattern


class TestTranslatedPattern:
    """Test class for TranslatedPattern."""

    @pytest.mark.parametrize(
        "data1,data2,expected_pattern",
        [
            ('1', '4', r'\d'),
            ('2', '44', r'\d+'),
            ('555', '4', r'\d+'),
            ('1.1', '4', r'\d*[.]?\d+'),
            ('12', '4.1', r'\d*[.]?\d+'),
            ('12.3', '4.1', r'\d*[.]?\d+'),
            ('3', '+4.4',  r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'),
            ('4', 'a', r'[a-zA-Z0-9]'),
            ('5', '-', r'\S'),
            ('5', '-+', r'\S+'),
            ('6', '- -', r'\S+( \S+)*'),
        ]
    )
    def test_recommend_pattern(self, data1, data2, expected_pattern):
        method = TranslatedPattern.recommend_pattern_using_data
        recommended_pat_obj = method(data1, data2)
        recommended_pat = recommended_pat_obj.pattern

        assert recommended_pat == expected_pattern

    @pytest.mark.parametrize(
        "data,var,expected_snippet",
        [
            ('1', '', 'digit(value=1)'),
            ('1', 'v1', 'digit(var=v1, value=1)'),
            ('123', 'v1', 'digits(var=v1, value=123)'),
            ('1.1', 'v1', 'number(var=v1, value=1.1)'),
            ('-1.1', 'v1', 'mixed_number(var=v1, value=-1.1)'),
            ('-', 'v1', 'punct(var=v1, value=-)'),
            ('(),', 'v1', 'puncts(var=v1, value=_SYMBOL_LEFT_PARENTHESIS__SYMBOL_RIGHT_PARENTHESIS_,)'),  # noqa
            ('( ) ,', 'v1', 'puncts_phrase(var=v1, value=_SYMBOL_LEFT_PARENTHESIS_ _SYMBOL_RIGHT_PARENTHESIS_ ,)'),    # noqa
            ('--  ---- ++++++', 'v1', 'puncts_group(var=v1, value=--  ---- ++++++)'),
            ('a', 'v1', 'letter(var=v1, value=a)'),
            ('ab', 'v1', 'letters(var=v1, value=ab)'),
            ('a1', 'v1', 'word(var=v1, value=a1)'),
            ('a1 b2', 'v1', 'phrase(var=v1, value=a1 b2)'),
            ('1.1.1.1', 'v1', 'mixed_word(var=v1, value=1.1.1.1)'),
            ('1.1.1.1 2::2', 'v1', 'mixed_phrase(var=v1, value=1.1.1.1 2::2)'),
        ]
    )
    def test_get_readable_snippet(self, data, var, expected_snippet):
        node = TranslatedPattern.do_factory_create(data)
        snippet = node.get_readable_snippet(var=var)
        assert snippet == expected_snippet
