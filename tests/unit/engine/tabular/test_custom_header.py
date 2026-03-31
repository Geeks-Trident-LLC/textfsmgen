"""
Unit tests for the `textfsmgen.engine.tabular.VarColumnTabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_custom_header.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_custom_header.py
"""


import re

from textwrap import dedent

from textfsmgen.libs.utils import get_data_as_tabular

from textfsmgen.engine.tabular import VarColumnTabularTranslator


def test_ex1():
    test_data = """
LastWriteTime          Name
---------------------- -------------------
9/1/2021 6:13:50 AM    reference
10/5/2021 9:13:50 PM   dsc
11/2/2021 11:58:45 PM  README.md
12/16/2021 12:30:59 PM CONTRIBUTING.md
                """.strip()

    expected_result = [
        {'col0': 'LastWriteTime', 'col1': 'Name'},
        {'col0': '9/1/2021 6:13:50 AM', 'col1': 'reference'},
        {'col0': '10/5/2021 9:13:50 PM', 'col1': 'dsc'},
        {'col0': '11/2/2021 11:58:45 PM', 'col1': 'README.md'},
        {'col0': '12/16/2021 12:30:59 PM', 'col1': 'CONTRIBUTING.md'}
    ]

    expected_result_as_tabular_text = """
+------------------------+-----------------+
| col0                   | col1            |
+------------------------+-----------------+
| LastWriteTime          | Name            |
| 9/1/2021 6:13:50 AM    | reference       |
| 10/5/2021 9:13:50 PM   | dsc             |
| 11/2/2021 11:58:45 PM  | README.md       |
| 12/16/2021 12:30:59 PM | CONTRIBUTING.md |
+------------------------+-----------------+
    """.strip()

    node = VarColumnTabularTranslator(
        test_data, column_count=2,
        custom_header_text='---------------------- ---------------'
    )
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
        {'col0': 'fruits', 'col1': 'meat', 'col2': 'drinks'},
        {'col0': 'orange', 'col1': 'pork', 'col2': 'water'},
        {'col0': 'peach', 'col1': '', 'col2': 'pepsi soda'}
    ]

    expected_result_as_tabular_text = """
+--------+------+------------+
| col0   | col1 | col2       |
+--------+------+------------+
| fruits | meat | drinks     |
| orange | pork | water      |
| peach  |      | pepsi soda |
+--------+------+------------+
    """.strip()

    node = VarColumnTabularTranslator(
        test_data, column_count=3,
        custom_header_text='--------- --------- ----------'
    )
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text
