"""
Unit tests for the `textfsmgen.gpdiff.DiffLinePattern` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpdiff/test_diff_line_pattern.py
    or
    $ python -m pytest tests/unit/gpdiff/test_diff_line_pattern.py
"""

import pytest

from textfsmgen.gpdiff import DiffLinePattern


class TestDiffLinePattern:
    """
    Test suite for DiffLinePattern.

    Covers line preparation, exception handling,
    pattern generation, and snippet generation.
    """

    @pytest.mark.parametrize(
        "lines, exp_count",
        [
            (['line 1', 'line 2'], 2),
            (['line 1', 'line 2', 'line 3'], 3),
            (['line 1', '', 'line 3', 'line4'], 3),
            (['line 1', '', '      ', 'line4'], 2),
        ]
    )
    def test_prepare(self, lines, exp_count):
        """Test line preparation and count of non-empty trimmed lines."""
        node = DiffLinePattern("a", "b")
        node.reset()
        node.prepare(*lines)
        assert len(node.lines) == exp_count

    @pytest.mark.parametrize(
        "lines",
        [
            ('line 1', ''),
            (' ', 'line2'),
            (' ', '    '),
            ('', ''),
        ]
    )
    def test_prepare_raises(self, lines):
        """Test that prepare raises an exception when insufficient valid lines are provided."""
        node = DiffLinePattern("a", "b")
        with pytest.raises(Exception):
            node.prepare(*lines)

    @pytest.mark.parametrize(
        "line_a, line_b, exp_pattern",
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
    def test_get_pattern_between_lines(self, line_a, line_b, exp_pattern):
        """Test pattern generation between two lines."""
        node = DiffLinePattern("a", "b")
        node.reset()
        pattern = node.get_pattern_btw_two_lines(line_a, line_b)
        assert pattern == exp_pattern

    @pytest.mark.parametrize(
        "lines, exp_pattern",
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
    def test_generated_pattern(self, lines, exp_pattern):
        """Test auto-generated pattern from multiple lines."""
        node = DiffLinePattern(*lines)
        assert node.pattern == exp_pattern

    @pytest.mark.parametrize(
        "lines, exp_snippet",
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
    def test_generated_snippet(self, lines, exp_snippet):
        """Test auto-generated snippet from multiple lines."""
        node = DiffLinePattern(*lines)
        assert node.snippet == exp_snippet


class TestDiffLinePatternSnippets:
    """
    Test suite for DiffLinePattern snippet and pattern generation.
    """

    def test_snippet_process_table_line(self):
        """Test snippet generation for process table lines."""
        lines = [
            "12345 | ttys000  |  0:00.55 | /bin/zsh --login -i",
            " 3344 | ttys001  |  0:01.23 | -zsh",
        ]
        exp_snip = (
            "start(space) digits(var_v0) | word(var_v1)  |  mixed_number(var_v2) "
            "| mixed_words(var_v3) end()"
        )
        node = DiffLinePattern(*lines)
        assert node.snippet == exp_snip

    def test_snippet_with_tab_space(self):
        """Test snippet generation when tab characters are present."""
        lines = [
            "this \t is a pen",
            "this is the yellow pen",
        ]
        exp_snip = "start() this\t is words(var_v0) pen end()"
        node = DiffLinePattern(*lines)
        assert node.snippet == exp_snip

    def test_snippet_ipv6_with_word_and_digits(self):
        """Test snippet generation for IPv6 address with word and digits."""
        lines = [
            "ipv6_addr: a::b % 16",
            "ipv6_addr: a::c % 32",
        ]
        exp_snip = "start() ipv6_addr: mixed_word(var_v0) % digits(var_v1) end()"
        node = DiffLinePattern(*lines)
        assert node.snippet == exp_snip

    def test_snippet_ipv6_with_phrase(self):
        """Test snippet generation for IPv6 address with phrase differences."""
        lines = [
            "ipv6_addr: 1::2 % 32",
            "ipv6_addr: 1::3 / 33",
        ]
        exp_snip = "start() ipv6_addr: non_whitespaces_phrase(var_v0) end()"
        node = DiffLinePattern(*lines)
        assert node.snippet == exp_snip

    def test_snippet_with_optional_letters(self):
        """Test snippet generation with optional letters in phrase."""
        lines = [
            "this is yellow half \t pencil",
            "this is red half pencil",
            "this is green half pencil",
            "this is half pencil",
        ]
        exp_snip = "start() this is letters(var_v0, or_empty) half\t pencil end()"
        node = DiffLinePattern(*lines)
        assert node.snippet == exp_snip

    def test_pattern_with_tab_space(self):
        """Test regex pattern generation when tab characters are present."""
        lines = [
            "this \t is a pen",
            "this is the yellow pen",
        ]
        exp_pat = (
            "this\\s+is (?P<v0>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*)*) pen"
        )
        node = DiffLinePattern(*lines)
        assert node.pattern == exp_pat