"""
Unit tests for the `textfsmgen.engine.tabular.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_misc_scenarios.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_misc_scenarios.py
"""

from textwrap import dedent
from textfsmgen.engine.tabular import TabularTranslator


def test_correctness_group_or_phrase():
    text = dedent("""
        fruits    meat      drinks
        ------    --------  -------
        orange    pork      water
        peach               pepsi soda
        mango     chicken
        """).strip()

    expected_tmpl_snippet = dedent("""
        fruits    meat      drinks
        start() word(var_fruits)  word(var_meat)  words(var_drinks) end() -> record
        start() word(var_fruits)  word(var_meat) end(space) -> record
        start() word(var_fruits) 10_15_space() words(var_drinks) end() -> record
        """).strip()

    node = TabularTranslator(text)
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_tmpl_snippet
