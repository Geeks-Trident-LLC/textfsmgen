"""
Unit tests for the `textfsmgen.gpiterative` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpiterative/test_iterative_line_pattern_class.py
    or
    $ python -m pytest tests/unit/gpiterative/test_iterative_line_pattern_class.py
"""

import pytest

from textfsmgen.gpiterative import IterativeLinePattern


class TestIterativeLinePattern:
    """Test class for TestIterativeLinePattern"""
    @pytest.mark.parametrize(
        "line,label,expected_snippet",
        [
            (
                'total oranges : 123', '',
                'capture() keep() action(): letters(var=v0, value=total) letters(var=v1, value=oranges) punct(var=v2, value=:) digits(var=v3, value=123)'     # noqa
            ),
            (
                'total oranges : 123', '0',
                'capture() keep() action(): letters(var=v00, value=total) letters(var=v01, value=oranges) punct(var=v02, value=:) digits(var=v03, value=123)'  # noqa
            ),
            (
                'utun0: flags=8051<UP,RUNNING> mtu 1380', '',
                'capture() keep() action(): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)'  # noqa
            ),
        ]
    )
    def test_get_editable_snippet(self, line, label, expected_snippet):
        node = IterativeLinePattern(line, label=label)
        snippet = node.symbolize()
        assert snippet == expected_snippet

    @pytest.mark.parametrize(
        "line,expected_snippet",
        [
            (
                'utun0: flags=8051<UP,RUNNING> mtu 1380',
                'capture() keep() action(): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)'  # noqa
            ),
            (
                'capture() keep() action(0-split, 1-split-=<>): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',   # noqa
                'capture() keep() action(): word(var=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(var=v8, value=8051)punct(var=v9, value=<)mixed_word(var=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(var=v3, value=1380)'   # noqa
            ),
            (
                'capture(4,8,10,3) keep() action(): word(var=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(var=v8, value=8051)punct(var=v9, value=<)mixed_word(var=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',  # noqa
                'capture() keep() action(): word(cvar=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(cvar=v8, value=8051)punct(var=v9, value=<)mixed_word(cvar=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(cvar=v3, value=1380)'   # noqa
            ),
        ]
    )
    def test_to_snippet(self, line, expected_snippet):
        node = IterativeLinePattern(line)
        snippet = node.to_snippet()
        assert snippet == expected_snippet

    @pytest.mark.parametrize(
        "lines_or_snippets,expected_snippets,expected_regex_pattern",
        [
            (
                (
                    'utun0: flags=8051<UP,RUNNING> mtu 1380',
                    'capture() keep() action(0-split, 1-split-=<>): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',   # noqa
                    'capture(4,8,10,3) keep() action(): word(var=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(var=v8, value=8051)punct(var=v9, value=<)mixed_word(var=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',  # noqa
                ),
                (
                    'capture() keep() action(): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',   # noqa
                    'capture() keep() action(): word(var=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(var=v8, value=8051)punct(var=v9, value=<)mixed_word(var=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',  # noqa
                    'capture() keep() action(): word(cvar=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(cvar=v8, value=8051)punct(var=v9, value=<)mixed_word(cvar=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(cvar=v3, value=1380)'   # noqa
                ),
                r'(?P<v4>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*): flags=(?P<v8>\d+)<(?P<v10>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)> mtu (?P<v3>\d+)'
            )
        ]
    )
    def test_to_regex(self, lines_or_snippets, expected_snippets, expected_regex_pattern):
        node = None
        for index, line_or_snippet in enumerate(lines_or_snippets):
            node = IterativeLinePattern(line_or_snippet)
            snippet = node.to_snippet()
            assert snippet == expected_snippets[index]
        regex_pattern = node.to_regex()
        assert regex_pattern == expected_regex_pattern

    @pytest.mark.parametrize(
        "lines_or_snippets,expected_snippets,expected_template_snippet",
        [
            (
                (
                    'utun0: flags=8051<UP,RUNNING> mtu 1380',
                    'capture() keep() action(0-split, 1-split-=<>): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',   # noqa
                    'capture(4,8,10,3) keep() action(): word(var=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(var=v8, value=8051)punct(var=v9, value=<)mixed_word(var=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',  # noqa
                ),
                (
                    'capture() keep() action(): mixed_word(var=v0, value=utun0:) mixed_word(var=v1, value=flags=8051<UP,RUNNING>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',   # noqa
                    'capture() keep() action(): word(var=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(var=v8, value=8051)punct(var=v9, value=<)mixed_word(var=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(var=v3, value=1380)',  # noqa
                    'capture() keep() action(): word(cvar=v4, value=utun0)punct(var=v5, value=:) letters(var=v6, value=flags)punct(var=v7, value==)digits(cvar=v8, value=8051)punct(var=v9, value=<)mixed_word(cvar=v10, value=UP,RUNNING)punct(var=v11, value=>) letters(var=v2, value=mtu) digits(cvar=v3, value=1380)'   # noqa
                ),
                r'word(var_v4): flags=digits(var_v8)<mixed_word(var_v10)> mtu digits(var_v3)'
            )
        ]
    )
    def test_to_template_snippet(self, lines_or_snippets, expected_snippets, expected_template_snippet):
        node = None
        for index, line_or_snippet in enumerate(lines_or_snippets):
            node = IterativeLinePattern(line_or_snippet)
            snippet = node.to_snippet()
            assert snippet == expected_snippets[index]
        tmpl_snippet = node.to_template_snippet()
        assert tmpl_snippet == expected_template_snippet

