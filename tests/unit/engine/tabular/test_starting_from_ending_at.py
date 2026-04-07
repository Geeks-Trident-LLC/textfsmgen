"""
Unit tests for the `textfsmgen.engine.tabular.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_starting_from_ending_at.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_starting_from_ending_at.py
"""

from textwrap import dedent
from textfsmgen.engine.tabular import TabularTranslator


def test_starting_from_and_ending_at_arguments():
    text = dedent("""
        line 1: blab 123 blab
        line 2: 1.1.2 blab blab
        index     col1            col2
        1         item1.1         item1.2
        2         item2.1         item2.2
        3         ?               item3.2
        line k: 123 blab blab
        index     col1            col2
        4         item4.1         item4.2
        5         item5.1         item5.2
        6         ?               item6.2
    """).strip()

    exp_snippet = dedent("""
        index     col1            col2 -> Table
        Table
        start() digits(var_index)  non_wss(var_col1)  mixed_word(var_col2) end() -> record
        line k: digits() blab blab -> EOF
    """).strip()
    translator = TabularTranslator(text, column_widths="10, 15,", starting_from=2, ending_at=6)
    snippet = translator.to_snippet()
    assert snippet == exp_snippet
