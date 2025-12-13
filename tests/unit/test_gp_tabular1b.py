# import re

import pytest           # noqa
# from textwrap import dedent

from genericlib import get_data_as_tabular

# from textfsmgen.core import verify
# from textfsmgen.core import get_textfsm_template

from textfsmgen.gptabular import TabularTextPatternByVarColumns


def test_to_tabular_custom_divider_ex1():
    test_data = """
LastWriteTime           Name
----------------------|--------------------
9/1/2021 6:13:50 AM   | reference
10/5/2021 9:13:50 PM  | dsc
11/2/2021 11:58:45 PM | README.md
12/16/2021 12:30:59 PM| CONTRIBUTING.md
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
    node = TabularTextPatternByVarColumns(test_data, divider='|', columns_count=2)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_custom_divider_ex2():
    test_data = """
fruits   | meat    | drinks
---------|---------|------------
orange   | pork    | water
peach    |         | pepsi soda
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

    node = TabularTextPatternByVarColumns(test_data, divider='|', columns_count=3)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_custom_divider_ex3():
    test_data = """
+------------+-------------+---------------+
| fruits     |    meat     |        drinks |
+------------+-------------+---------------+
| orange     |    pork     |         water |
| peach      |             |    pepsi soda |
+------------+-------------+---------------+
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

    node = TabularTextPatternByVarColumns(test_data, divider='|', columns_count=3)
    table = node.parse_table()
    assert table
    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_custom_divider_ex4():
    test_data = """
+------------+-------------+---------------
| fruits     |    meat     |        drinks        
+------------+-------------+---------------
| orange     |    pork     |         water 
| peach      |             |    pepsi soda 
+------------+-------------+---------------
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

    node = TabularTextPatternByVarColumns(test_data, divider='|', columns_count=3)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text
