"""
Unit tests for the `textfsmgen.engine.tabular.VarColumnTabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_multi_space_divider.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_multi_space_divider.py
"""


import re

from textwrap import dedent

from textfsmgen.libs.utils import get_data_as_tabular

from textfsmgen.engine.tabular import VarColumnTabularTranslator


def test_ex1():
    test_data = """
LastWriteTime          Name
9/1/2021 6:13:50 AM    reference
10/5/2021 9:13:50 PM   dsc
11/2/2021 11:58:45 PM  README.md
12/16/2021 12:30:59 PM CONTRIBUTING.md
                """.strip()

    expected_result = [
        {'lastwritetime': '9/1/2021 6:13:50 AM', 'name': 'reference'},
        {'lastwritetime': '10/5/2021 9:13:50 PM', 'name': 'dsc'},
        {'lastwritetime': '11/2/2021 11:58:45 PM', 'name': 'README.md'},
        {'lastwritetime': '12/16/2021 12:30:59 PM', 'name': 'CONTRIBUTING.md'}
    ]

    expected_result_as_tabular_text = """
+------------------------+-----------------+
| lastwritetime          | name            |
+------------------------+-----------------+
| 9/1/2021 6:13:50 AM    | reference       |
| 10/5/2021 9:13:50 PM   | dsc             |
| 11/2/2021 11:58:45 PM  | README.md       |
| 12/16/2021 12:30:59 PM | CONTRIBUTING.md |
+------------------------+-----------------+
    """.strip()

    node = VarColumnTabularTranslator(test_data, column_divider='  ', column_count=2)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_ex2():
    test_data = """
fruits    meat      drinks
orange    pork      water
peach               pepsi soda
                """.strip()

    expected_result = [
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'}
    ]

    expected_result_as_tabular_text = """
+--------+------+------------+
| fruits | meat | drinks     |
+--------+------+------------+
| orange | pork | water      |
| peach  |      | pepsi soda |
+--------+------+------------+
    """.strip()

    node = VarColumnTabularTranslator(test_data, column_divider='  ', column_count=3)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text

