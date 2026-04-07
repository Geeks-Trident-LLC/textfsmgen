"""
Unit tests for the `textfsmgen.engine.tabular.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_calculating_max_widths.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_calculating_max_widths.py
"""

from textwrap import dedent
from textfsmgen.engine.tabular import TabularTranslator



def test():
    text = dedent("""
        a        b
        -------- -------
        val1.1   val1.2
                 val2.2
        val3.1         
        val4.1   val4.2
        val5.1
    """).strip()

    exp_snippet = dedent("""
        a        b
        start() mixed_word(var_a)  mixed_word(var_b) end(space) -> record
        start() mixed_word(var_a) end(space) -> record
        start() 7_9_space() mixed_word(var_b) end(space) -> record
    """).strip()

    translator = TabularTranslator(text)
    snippet = translator.to_snippet()
    assert snippet == exp_snippet


def test_other_case():
    text = dedent("""
a        b       c
-------- ------- -------
val1.1   val1.2  val1.3
         val2.2  val2.3
val3.1           val3.3
                 val4.3
val5.1   val5.2
         val6.2
val7.1
    """).strip()

    exp_snippet = dedent("""
a        b       c
start() mixed_word(var_a)  mixed_word(var_b)  mixed_word(var_c) end() -> record
start() mixed_word(var_a)  mixed_word(var_b) end(space) -> record
start() mixed_word(var_a) 8_11_space() mixed_word(var_c) end() -> record
start() mixed_word(var_a) end(space) -> record
start() 7_9_space() mixed_word(var_b)  mixed_word(var_c) end() -> record
start() 7_9_space() mixed_word(var_b) end(space) -> record
start() 15_17_space() mixed_word(var_c) end() -> record
    """).strip()

    translator = TabularTranslator(text)
    snippet = translator.to_snippet()
    assert snippet == exp_snippet
