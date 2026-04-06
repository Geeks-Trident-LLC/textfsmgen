"""
Unit tests for the `textfsmgen.engine.tabular.VarColumnTabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_custom_divider.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_custom_divider.py
"""


import re

from textwrap import dedent
from textfsmgen.engine.tabular import VarColumnTabularTranslator
from textfsmgen.core.verify import verify


def test_ex1():
    test_data = dedent("""
        LastWriteTime           Name
        -----------------------|--------------------
        9/1/2021 6:13:50 AM    | reference
        10/5/2021 9:13:50 PM   | dsc
        11/2/2021 11:58:45 PM  | README.md
        12/16/2021 12:30:59 PM | CONTRIBUTING.md
                """).strip()

    expected_snippet = dedent("""
        LastWriteTime           Name
        start() 3_mixed_word(var_lastwritetime)optional_spaces()|optional_spaces()mixed_word(var_name) end() -> record
    """).strip()

    expected_result = [
        {'lastwritetime': '9/1/2021 6:13:50 AM', 'name': 'reference'},
        {'lastwritetime': '10/5/2021 9:13:50 PM', 'name': 'dsc'},
        {'lastwritetime': '11/2/2021 11:58:45 PM', 'name': 'README.md'},
        {'lastwritetime': '12/16/2021 12:30:59 PM', 'name': 'CONTRIBUTING.md'}
    ]

    node = VarColumnTabularTranslator(
        test_data,
        column_divider='|',
        column_count=2
    )
    table = node.parse_table()
    assert table

    template_snippet = table.to_template_snippet()
    assert template_snippet == expected_snippet

    ok = verify(template_snippet, test_data, expected_result=expected_result)
    assert ok


def test_ex2():
    test_data = dedent("""
        fruits   | meat    | drinks
        ---------|---------|------------
        orange   | pork    | water
        peach    |         | pepsi soda
                """).strip()

    expected_snippet = dedent("""
        fruits   | meat    | drinks
        start() word(var_fruits)optional_spaces()|optional_spaces()word(var_meat, or_empty)optional_spaces()|optional_spaces()words(var_drinks) end() -> record
    """).strip()

    expected_result = [
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'}
    ]

    node = VarColumnTabularTranslator(
        test_data,
        column_divider='|',
        column_count=3
    )
    table = node.parse_table()
    assert table

    template_snippet = table.to_template_snippet()
    assert template_snippet == expected_snippet

    ok = verify(template_snippet, test_data, expected_result=expected_result)
    assert ok


def test_ex3():
    test_data = dedent("""
        +------------+-------------+---------------+
        | fruits     |    meat     |        drinks |
        +------------+-------------+---------------+
        | orange     |    pork     |         water |
        | peach      |             |    pepsi soda |
        +------------+-------------+---------------+
                """).strip()

    expected_snippet = dedent("""
        | fruits     |    meat     |        drinks |
        start() |optional_spaces()word(var_fruits)optional_spaces()|optional_spaces()word(var_meat, or_empty)optional_spaces()|optional_spaces()words(var_drinks)optional_spaces()| end() -> record
    """).strip()

    expected_result = [
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'}
    ]

    node = VarColumnTabularTranslator(
        test_data,
        column_divider='|',
        column_count=3
    )
    table = node.parse_table()
    assert table

    template_snippet = table.to_template_snippet()
    assert template_snippet == expected_snippet

    ok = verify(template_snippet, test_data, expected_result=expected_result)
    assert ok


def test_ex4():
    test_data = dedent("""
        +------------+-------------+---------------
        | fruits     |    meat     |        drinks        
        +------------+-------------+---------------
        | orange     |    pork     |         water 
        | peach      |             |    pepsi soda 
        +------------+-------------+---------------
                """).strip()

    expected_snippet = dedent("""
        | fruits     |    meat     |        drinks        
        start() |optional_spaces()word(var_fruits)optional_spaces()|optional_spaces()word(var_meat, or_empty)optional_spaces()|optional_spaces()words(var_drinks) end(space) -> record
    """).strip()

    expected_result = [
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'}
    ]

    node = VarColumnTabularTranslator(
        test_data,
        column_divider='|',
        column_count=3
    )
    table = node.parse_table()
    assert table

    template_snippet = table.to_template_snippet()
    assert template_snippet == expected_snippet

    ok = verify(template_snippet, test_data, expected_result=expected_result)
    assert ok


def test_ex5():
    test_data = dedent("""
        -----------+-------------+---------------+
        fruits     |    meat     |        drinks |
        -----------+-------------+---------------+
        orange     |    pork     |         water |
        peach      |             |    pepsi soda |
        -----------+-------------+---------------+
                """).strip()

    expected_snippet = dedent("""
        fruits     |    meat     |        drinks |
        start() word(var_fruits)optional_spaces()|optional_spaces()word(var_meat, or_empty)optional_spaces()|optional_spaces()words(var_drinks)optional_spaces()| end() -> record
    """).strip()

    expected_result = [
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'}
    ]

    node = VarColumnTabularTranslator(
        test_data,
        column_divider='|',
        column_count=3
    )
    table = node.parse_table()
    assert table

    template_snippet = table.to_template_snippet()
    assert template_snippet == expected_snippet

    ok = verify(template_snippet, test_data, expected_result=expected_result)
    assert ok


# def test_ex6():
#     test_data = dedent("""
#         fruits|meat|drinks
#         orange|pork|water
#         peach||pepsi soda
#                 """).strip()
#
#     expected_snippet = dedent("""
#     """).strip()
#
#     expected_result = [
#         {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
#         {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'}
#     ]
#
#     node = VarColumnTabularTranslator(
#         test_data,
#         column_divider='|',
#         column_count=3,
#         has_header_row=True
#     )
#     table = node.parse_table()
#     assert table
#
#     template_snippet = table.to_template_snippet()
#     breakpoint()
#     assert template_snippet == expected_snippet
#
#     ok = verify(template_snippet, test_data, expected_result=expected_result)
#     assert ok