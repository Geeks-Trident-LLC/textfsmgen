"""
Unit tests for the `textfsmgen.engine.translate.PatternTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_pattern_translator_class.py
    or
    $ python -m pytest tests/unit/translate/test_pattern_translator_class.py
"""

import pytest

from textfsmgen.engine.translate import make_translator

from tests.unit.engine.translate import to_list


class TestGetReadableSnippetMethod:
    """Test suite for PatternTranslator.get_readable_snippet."""

    @pytest.mark.parametrize(
        "digits, var_name, expected_snippet, expected_pattern",
        [
            (
                "1",
                "v1",
                "digit(var=v1, value=1)",  # expected snippet
                r"\d",  # expected pattern
            ),
            (
                "123",
                "v1",
                "digits(var=v1, value=123)",  # expected snippet
                r"\d+",  # expected pattern
            ),
        ],
    )
    def test_digits(self, digits, var_name, expected_snippet, expected_pattern):
        args = to_list(digits)
        node = make_translator(*args)
        snippet = node.to_readable_snippet(var=var_name)
        assert snippet == expected_snippet
        assert node.pattern == expected_pattern

    @pytest.mark.parametrize(
        "number, var_name, expected_snippet, expected_pattern",
        [
            (
                "1.1",
                "v1",
                "number(var=v1, value=1.1)",  # expected snippet
                r"\d*[.]?\d+",  # expected pattern
            ),
            (
                "-11",
                "v1",
                "mixed_number(var=v1, value=-11)",  # expected snippet
                r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*",  # expected pattern
            ),
            (
                "+11",
                "v1",
                "mixed_number(var=v1, value=+11)",  # expected snippet
                r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*",  # expected pattern
            ),
            (
                "-1.1",
                "v1",
                "mixed_number(var=v1, value=-1.1)",  # expected snippet
                r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*",  # expected pattern
            ),
            (
                "(1.1)",
                "v1",
                # expected snippet
                "mixed_number(var=v1, value=_SYMBOL_LEFT_PARENTHESIS_1.1_SYMBOL_RIGHT_PARENTHESIS_)",
                # expected pattern
                r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*",
            ),
        ],
    )
    def test_number(self, number, var_name, expected_snippet, expected_pattern):
        args = to_list(number)
        node = make_translator(*args)
        snippet = node.to_readable_snippet(var=var_name)
        assert snippet == expected_snippet
        assert node.pattern == expected_pattern

    @pytest.mark.parametrize(
        "puncts, var_name, expected_snippet, expected_pattern",
        [
            (
                "-",
                "v1",
                "punct(var=v1, value=-)",  # expected snippet
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]",  # expected pattern
            ),
            (
                ["-", "++"],
                "v1",
                "puncts(var=v1, value=-)",  # expected snippet
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+",  # expected pattern
            ),
            (
                "+-*",
                "v1",
                "puncts(var=v1, value=+-*)",  # expected snippet
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+",  # expected pattern
            ),
            (
                "()",
                "v1",
                # expected snippet
                "puncts(var=v1, value=_SYMBOL_LEFT_PARENTHESIS__SYMBOL_RIGHT_PARENTHESIS_)",
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+",  # expected pattern
            ),
            (
                "(-)",
                "v1",
                # expected snippet
                "puncts(var=v1, value=_SYMBOL_LEFT_PARENTHESIS_-_SYMBOL_RIGHT_PARENTHESIS_)",
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+",  # expected pattern
            ),
            (
                ["--", "== +++"],
                "v1",
                "puncts_items(var=v1, value=--)",  # expected snippet
                # expected pattern
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+(\s+[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+)*",
            ),
            (
                "--  === ++++++",
                "v1",
                "puncts_group(var=v1, value=--  === ++++++)",  # expected snippet
                # expected pattern
                r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+(\s+[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+)+",
            ),
        ],
    )
    def test_punctuations(self, puncts, var_name, expected_snippet, expected_pattern):
        args = to_list(puncts)
        node = make_translator(*args)
        snippet = node.to_readable_snippet(var=var_name)
        assert snippet == expected_snippet
        assert node.pattern == expected_pattern

    @pytest.mark.parametrize(
        "text, var_name, expected_snippet, expected_pattern",
        [
            (
                "a",
                "v1",
                "letter(var=v1, value=a)",  # expected snippet
                "[a-zA-Z]",  # expected pattern
            ),
            (
                "abc",
                "v1",
                "letters(var=v1, value=abc)",  # expected snippet
                "[a-zA-Z]+",  # expected pattern
            ),
            (
                "var1",
                "v1",
                "word(var=v1, value=var1)",  # expected snippet
                r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*",  # expected pattern
            ),
            (
                ["var1", "var1 var2"],
                "v1",
                "words(var=v1, value=var1)",  # expected snippet
                r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)*",  # expected pattern
            ),
            (
                "ab cd",
                "v1",
                "word_group(var=v1, value=ab cd)",  # expected snippet
                r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)+",  # expected pattern
            ),
            (
                "1.1.1.1",
                "v1",
                "mixed_word(var=v1, value=1.1.1.1)",  # expected snippet
                r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*",  # expected pattern
            ),
            (
                ["1.1.1.1", "1.1.1.1 2.2.2.2"],
                "v1",
                "mixed_words(var=v1, value=1.1.1.1)",  # expected snippet
                # expected pattern
                r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*",
            ),
            (
                "1.1.1.1 2.2.2.2",
                "v1",
                "mixed_word_group(var=v1, value=1.1.1.1 2.2.2.2)",  # expected snippet
                # expected pattern
                r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+",
            ),
        ],
    )
    def test_creating_text_snippet(
        self, text, var_name, expected_snippet, expected_pattern
    ):
        args = to_list(text)
        node = make_translator(*args)
        snippet = node.to_readable_snippet(var=var_name)
        assert snippet == expected_snippet
        assert node.pattern == expected_pattern

    @pytest.mark.parametrize(
        "data, var_name, expected_snippet, expected_pattern",
        [
            (
                ["a", "1", "#"],
                "v1",
                "graph(var=v1, value=a)",  # expected snippet
                r"[\x21-\x7e]",  # expected pattern
            ),
        ],
    )
    def test_creating_graph_snippet(
        self, data, var_name, expected_snippet, expected_pattern
    ):
        args = to_list(data)
        node = make_translator(*args)
        snippet = node.to_readable_snippet(var=var_name)
        assert snippet == expected_snippet
        assert node.pattern == expected_pattern

    @pytest.mark.parametrize(
        "data, var_name, expected_snippet, expected_pattern",
        [
            (["a", "1", "\xc8"], "v1", "non_ws(var=v1, value=a)", r"\S"),
            (["abc", "123", "-+"], "v1", "non_wss(var=v1, value=abc)", r"\S+"),
            (
                ["abc", "123", "---- ++++"],
                "v1",
                "non_wss_items(var=v1, value=abc)",
                r"\S+(\s+\S+)*",
            ),
            (
                ["abc xyz", "123 456", "---- ++++"],
                "v1",
                "non_wss_group(var=v1, value=abc xyz)",
                r"\S+(\s+\S+)+",
            ),
        ],
    )
    def test_creating_non_white_space_snippet(
        self, data, var_name, expected_snippet, expected_pattern
    ):
        args = to_list(data)
        node = make_translator(*args)
        snippet = node.to_readable_snippet(var=var_name)
        assert snippet == expected_snippet
        assert node.pattern == expected_pattern
