import pytest           # noqa
from textwrap import dedent
from textfsmgenerator.gptabular import TabularTextPattern


def test_fixed_columns():
    text = dedent("""
        index     col1            col2
        1         item1.1         item1.2
        2         item2.1         item2.2
        3         ?               item3.2
    """).strip()

    expected_tmpl_snippet = dedent("""
        index     col1            col2
        start() digit(var_index)  non_whitespaces(var_col)  mixed_word(var_col2) end() -> record
    """).strip()

    node = TabularTextPattern(text, col_widths="10, 15,")
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet

