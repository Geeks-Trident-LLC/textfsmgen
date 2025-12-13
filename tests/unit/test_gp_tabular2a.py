import pytest           # noqa
from textwrap import dedent

from textfsmgen.gptabular import TabularTextPattern


def test_tabular_calculating_max_width():
    text = dedent("""
a        b      
-------- -------
val1.1   val1.2
         val2.2
val3.1
val4.1   val4.2
val5.1
    """).strip()

    expected_tmpl_snippet = dedent("""
a        b      
start() mixed_word(var_a)  mixed_word(var_b) end(space) -> record
start() mixed_word(var_a) end(space) -> record
start() space(repetition_7_9) mixed_word(var_b) end(space) -> record
    """).strip()

    node = TabularTextPattern(text)
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet
