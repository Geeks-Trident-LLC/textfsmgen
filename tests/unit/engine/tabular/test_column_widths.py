"""
Unit tests for the `textfsmgen.engine.tabular.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_column_widths.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_column_widths.py
"""

from textwrap import dedent
from textfsmgen.engine.tabular import TabularTranslator


def test():
    text = dedent("""
        index     col1            col2
        1         item1.1         item1.2
        2         item2.1         item2.2
        3         ?               item3.2
    """).strip()

    expected_tmpl_snippet = dedent("""
        index     col1            col2
        start() digits(var_index)  non_wss(var_col1)  mixed_word(var_col2) end() -> record
    """).strip()

    node = TabularTranslator(text, column_widths="10, 15,")
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet

