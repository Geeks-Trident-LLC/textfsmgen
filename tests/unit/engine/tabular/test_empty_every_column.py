"""
Unit tests for the `textfsmgen.engine.tabular.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_empty_every_column.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_empty_every_column.py
"""

from textwrap import dedent
from textfsmgen.engine.tabular import TabularTranslator


def test():
    text = dedent("""
one       two       three
--------  --------  ----------
item1.1   item1.2   item1.3
item2.1   item2.2
item3.1             item3.3
          item4.2   item4.3
item5.1
          item6.2
                    item7.3
    """).strip()

    expected_tmpl_snippet = dedent("""
one       two       three
start() mixed_word(var_one)  mixed_word(var_two)  mixed_word(var_three) end() -> record
start() mixed_word(var_one)  mixed_word(var_two) end(space) -> record
start() mixed_word(var_one) 10_13_space() mixed_word(var_three) end() -> record
start() mixed_word(var_one) end(space) -> record
start() 8_10_space() mixed_word(var_two)  mixed_word(var_three) end() -> record
start() 8_10_space() mixed_word(var_two) end(space) -> record
start() 18_20_space() mixed_word(var_three) end() -> record
    """).strip()    # noqa

    node = TabularTranslator(text)
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet

