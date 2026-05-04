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

    exp_snippet = dedent("""
        index     col1            col2
        start() digits(var_index)  non_wss(var_col1)  mixed_word(var_col2) end() -> record
    """).strip()

    translator = TabularTranslator(text, column_widths="10, 15,")
    snippet = translator.to_snippet()
    assert snippet == exp_snippet
