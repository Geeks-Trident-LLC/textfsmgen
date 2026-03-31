"""
Unit tests for the `textfsmgen.engine.tabular.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_user_marker.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_user_marker.py
"""

from textwrap import dedent
from textfsmgen.engine.tabular import TabularTranslator


def test_mark_one_line():
    text = dedent("""
a        b       c
-------- ------- -------------
val1.1   val1.2  val1.3
<user-marker-one-line>val2.1-very-long-text
         val2.2  val2.3
val3.1   val3.2  val3.3
    """).strip()

    expected_tmpl_snippet = dedent("""
a        b       c
start() mixed_word(var_a) end(space) -> Next
start() 5_9_space() mixed_word(var_b)  mixed_word(var_c) end() -> record
start() mixed_word(var_a)  mixed_word(var_b)  mixed_word(var_c) end() -> record
    """).strip()

    node = TabularTranslator(text)
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet


def test_mark_multi_line():
    text = dedent("""
a        b       c
-------- ------- -------------
val1.1   val1.2  val1.3
<user-marker-multi-line>val2.1   val2.2  val2.3
                 continue-val2.4
                 continue-val2.5
val3.1   val3.2  val3.3
    """).strip()

    expected_tmpl_snippet = dedent("""
a        b       c
start() mixed_word()optional_spaces() -> continue.record
start() mixed_word(var_a)  mixed_word(var_b)  mixed_word(var_c, meta_data_list) end(space) -> continue
start() 13_19_space() mixed_word(var_c, meta_data_list) end(space) -> continue
    """).strip()

    node = TabularTranslator(text)
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet
