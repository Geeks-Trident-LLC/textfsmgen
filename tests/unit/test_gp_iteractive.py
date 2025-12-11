import re

import pytest           # noqa
from textwrap import dedent

from textfsmgenerator.core import verify
from textfsmgenerator.core import get_textfsm_template

from textfsmgenerator.gpiteractive import IterativeLinePattern, IterativeLinesPattern


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
                r'(?P<v4>[a-zA-Z][a-zA-Z0-9]*): flags=(?P<v8>\d+)<(?P<v10>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)> mtu (?P<v3>\d+)'
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


class TestIterativeLinesPattern:
    """Test class for TestIterativeLinesPattern"""
    @pytest.mark.parametrize(
        "lst_of_text,expected_snippet",
        [
            (
                [
                    dedent("""
                        blab blab blab
                        fruits: orange, peach
                        meat: chicken, fish
                        blab *++ ???blab*?+
                    """).strip(),

                    dedent("""
                        capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                        capture() keep() action(11:12-join): mixed_word(var=v10, value=fruits:) mixed_word(var=v11, value=orange,) letters(var=v12, value=peach)
                        capture() keep() action(21:22-join): mixed_word(var=v20, value=meat:) mixed_word(var=v21, value=chicken,) letters(var=v22, value=fish)
                        capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                    """).strip(),

                    dedent("""
                        capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                        capture(11) keep() action(): mixed_word(var=v10, value=fruits:) mixed_words(var=v11, value=orange, peach)
                        capture(21) keep() action(): mixed_word(var=v20, value=meat:) mixed_words(var=v21, value=chicken, fish)
                        capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                    """).strip()
                 ],

                dedent("""
                    capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                    capture() keep() action(): mixed_word(var=v10, value=fruits:) mixed_words(cvar=v11, value=orange, peach)
                    capture() keep() action(): mixed_word(var=v20, value=meat:) mixed_words(cvar=v21, value=chicken, fish)
                    capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                """).strip()
            ),
        ]
    )
    def test_to_snippet(self, lst_of_text, expected_snippet):
        node = None
        for txt in lst_of_text:
            node = IterativeLinesPattern(txt)
        snippet = node.to_snippet()
        assert snippet == expected_snippet

    @pytest.mark.parametrize(
        "lst_of_text,expected_regex_pattern",
        [
            (
                [
                    dedent("""
                        blab blab blab
                        fruits: orange, peach
                        meat: chicken, fish
                        blab *++ ???blab*?+
                    """).strip(),

                    dedent("""
                        capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                        capture() keep() action(11:12-join): mixed_word(var=v10, value=fruits:) mixed_word(var=v11, value=orange,) letters(var=v12, value=peach)
                        capture() keep() action(21:22-join): mixed_word(var=v20, value=meat:) mixed_word(var=v21, value=chicken,) letters(var=v22, value=fish)
                        capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                    """).strip(),

                    dedent("""
                        capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                        capture(11) keep() action(): mixed_word(var=v10, value=fruits:) mixed_words(var=v11, value=orange, peach)
                        capture(21) keep() action(): mixed_word(var=v20, value=meat:) mixed_words(var=v21, value=chicken, fish)
                        capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                    """).strip()
                 ],
                r'blab blab blab(\r?\n|\r)fruits: (?P<v11>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*( [\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)(\r?\n|\r)meat: (?P<v21>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*( [\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)(\r?\n|\r)blab \*\+{2,} \?\?\?blab\*\?\+'     # noqa
            ),
        ]
    )
    def test_to_regex(self, lst_of_text, expected_regex_pattern):
        node = None
        for txt in lst_of_text:
            node = IterativeLinesPattern(txt)
        pattern = node.to_regex()
        assert pattern == expected_regex_pattern

        first_txt = lst_of_text[0]
        match = re.match(expected_regex_pattern, first_txt)
        assert match

    @pytest.mark.parametrize(
        "lst_of_text,expected_template_snippet,expected_template,expected_rows_count,expected_result",
        [
            (
                [
                    dedent("""
                        blab blab blab
                        fruits: orange, peach
                        meat: chicken, fish
                        blab *++ ???blab*?+
                    """).strip(),

                    dedent("""
                        capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                        capture() keep() action(11:12-join): mixed_word(var=v10, value=fruits:) mixed_word(var=v11, value=orange,) letters(var=v12, value=peach)
                        capture() keep() action(21:22-join): mixed_word(var=v20, value=meat:) mixed_word(var=v21, value=chicken,) letters(var=v22, value=fish)
                        capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                    """).strip(),

                    dedent("""
                        capture() keep() action(): letters(var=v0, value=blab) letters(var=v1, value=blab) letters(var=v2, value=blab)
                        capture(11) keep() action(): mixed_word(var=v10, value=fruits:) mixed_words(var=v11, value=orange, peach)
                        capture(21) keep() action(): mixed_word(var=v20, value=meat:) mixed_words(var=v21, value=chicken, fish)
                        capture() keep() action(): letters(var=v30, value=blab) puncts(var=v31, value=*++) mixed_word(var=v32, value=???blab*?+)
                    """).strip()
                 ],
                dedent("""
                    blab blab blab
                    fruits: mixed_words(var_v11)
                    meat: mixed_words(var_v21)
                    blab *++ ???blab*?+
                """).strip(),
                dedent(r"""
                    ################################################################################
                    # Template is generated by template Community Edition
                    # Created date: YYYY-mm-dd
                    ################################################################################
                    Value v11 ([\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*( [\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)
                    Value v21 ([\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*( [\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)
                    
                    Start
                      ^blab blab blab
                      ^fruits: ${v11}
                      ^meat: ${v21}
                      ^blab \*\+{2,} \?\?\?blab\*\?\+
                """).strip(),
                1,
                [{'v11': 'orange, peach', 'v21': 'chicken, fish'}]
            ),
        ]
    )
    def test_to_template_snippet(
        self, lst_of_text, expected_template_snippet,
        expected_template, expected_rows_count, expected_result
    ):
        node = None
        for txt in lst_of_text:
            node = IterativeLinesPattern(txt)
        tmpl_snippet = node.to_template_snippet()
        assert tmpl_snippet == expected_template_snippet
        template = get_textfsm_template(tmpl_snippet)
        template = re.sub(r'date: \d{4}-\d\d-\d\d', 'date: YYYY-mm-dd', template)
        assert template == expected_template

        test_data = lst_of_text[0]
        is_verified = verify(tmpl_snippet, test_data,
                             expected_result=expected_result)
        assert is_verified
