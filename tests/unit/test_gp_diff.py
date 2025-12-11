import pytest           # noqa

from textfsmgenerator.gpdiff import DiffLinePattern


class TestDiffLinePattern:
    """Test class for DiffLinePattern"""
    @pytest.mark.parametrize(
        "lines,expected_total_lines_count",
        [
            (['line 1', 'line 2'], 2),
            (['line 1', 'line 2', 'line 3'], 3),
            (['line 1', '', 'line 3', 'line4'], 3),
            (['line 1', '', '      ', 'line4'], 2),
        ]
    )
    def test_prepare(self, lines, expected_total_lines_count):
        node = DiffLinePattern('a', 'b')
        node.reset()
        node.prepare(*lines)
        total_lines_count = len(node.lines)
        assert total_lines_count == expected_total_lines_count

    @pytest.mark.parametrize(
        "lines",
        [
            ('line 1', ''),
            (' ', 'line2'),
            (' ', '    '),
            ('', ''),
        ]
    )
    def test_prepare_catch_exception(self, lines):
        node = DiffLinePattern('a', 'b')

        with pytest.raises(Exception):
            node.prepare(*lines)

    @pytest.mark.parametrize(
        "line_a,line_b,expected_pattern",
        [
            ('a', '@', r'(?P<v0>[\x21-\x7e])'),
            ('a b', '@', '(?P<v0>\\S+( +\\S+)*)'),
            ('a b', 'x','(?P<v0>[a-zA-Z][a-zA-Z0-9]*( +[a-zA-Z][a-zA-Z0-9]*)*)'),
            (
                'line one is a first line',
                'line ore is a second line',
                'line +(?P<v0>[a-zA-Z]+) +is +a +(?P<v1>[a-zA-Z]+) +line'
            ),
            (
                '  line one is a first line',
                'line ore is a second line',
                ' *line +(?P<v0>[a-zA-Z]+) +is +a +(?P<v1>[a-zA-Z]+) +line'
            ),
            (
                '  line one is a first line',
                '    line ore is a second line',
                ' +line +(?P<v0>[a-zA-Z]+) +is +a +(?P<v1>[a-zA-Z]+) +line'
            ),
            (
                '  line one is a first line  ',
                '    line ore is a second line',
                ' +line +(?P<v0>[a-zA-Z]+) +is +a +(?P<v1>[a-zA-Z]+) +line *'
            ),
            (
                'this line one is a first line',
                'line ore is a second bad line',
                '(?P<v0>([a-zA-Z]+)|)( +)?line +(?P<v1>[a-zA-Z]+) +is +a +(?P<v2>[a-zA-Z][a-zA-Z0-9]*( +[a-zA-Z][a-zA-Z0-9]*)*) +line'    # noqa
            ),
        ]
    )
    def test_get_pattern_btw_two_lines(self, line_a, line_b, expected_pattern):
        node = DiffLinePattern('a', 'b')
        node.reset()
        pattern = node.get_pattern_btw_two_lines(line_a, line_b)
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "lines,expected_pattern",
        [
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                 ),
                'this is (?P<v0>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*) pen'
            ),
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                    'this is the good yellow pen',
                ),
                'this is (?P<v0>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*) pen'
            ),
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                    'this is the good yellow pen',
                    'that is a pencil'
                ),
                '(?P<v0>[a-zA-Z]+) is (?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+)'
            ),
            (
                (
                    'this is a pen',
                    '  this is the yellow pen',
                    'this is the good yellow pen',
                    'that is a pencil'
                ),
                ' *(?P<v0>[a-zA-Z]+) is (?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+)'
            ),
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                    'this is the good yellow pen  ',
                    ' that is a pencil'
                ),
                ' *(?P<v0>[a-zA-Z]+) is (?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+) *'
            ),
            (
                (
                    '  this is a pen',
                    '    this is the yellow pen',
                    '  this is the good yellow pen ',
                    '    that is a pencil'
                ),
                ' +(?P<v0>[a-zA-Z]+) is (?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+) *'
            ),
            (
                (
                    '  this is a pen               ',
                    '    this is the yellow pen    ',
                    '  this is the good yellow pen ',
                    '    that is a pencil          '
                ),
                ' +(?P<v0>[a-zA-Z]+) is (?P<v1>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)+) +'
            ),
        ]
    )
    def test_generated_pattern(self, lines, expected_pattern):
        node = DiffLinePattern(*lines)
        pattern = node.pattern
        assert pattern == expected_pattern

    @pytest.mark.parametrize(
        "lines,expected_snippet",
        [
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                 ),
                'start() this is words(var_v0) pen end()'
            ),
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                    'this is the good yellow pen',
                ),
                'start() this is words(var_v0) pen end()'
            ),
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                    'this is the good yellow pen',
                    'that is a pencil'
                ),
                'start() letters(var_v0) is phrase(var_v1) end()'
            ),
            (
                (
                    'this is a pen',
                    '  this is the yellow pen',
                    'this is the good yellow pen',
                    'that is a pencil'
                ),
                'start(space) letters(var_v0) is phrase(var_v1) end()'
            ),
            (
                (
                    'this is a pen',
                    'this is the yellow pen',
                    'this is the good yellow pen  ',
                    ' that is a pencil'
                ),
                'start(space) letters(var_v0) is phrase(var_v1) end(space)'
            ),
            (
                (
                    '  this is a pen',
                    '    this is the yellow pen',
                    '  this is the good yellow pen ',
                    '    that is a pencil'
                ),
                'start(spaces) letters(var_v0) is phrase(var_v1) end(space)'
            ),
            (
                (
                    '  this is a pen               ',
                    '    this is the yellow pen    ',
                    '  this is the good yellow pen ',
                    '    that is a pencil          '
                ),
                'start(spaces) letters(var_v0) is phrase(var_v1) end(spaces)'
            ),
        ]
    )
    def test_generated_snippet(self, lines, expected_snippet):
        node = DiffLinePattern(*lines)
        snippet = node.snippet
        assert snippet == expected_snippet
