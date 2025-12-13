import re

import pytest           # noqa
from textwrap import dedent

from genericlib import get_data_as_tabular

from textfsmgen.core import verify
from textfsmgen.core import get_textfsm_template

from textfsmgen.gptabular import TabularTextPatternByVarColumns


def test_to_tabular_multi_spaces_divider_ex1():
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

    node = TabularTextPatternByVarColumns(test_data, divider='  ', columns_count=2)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_multi_spaces_divider_ex2():
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

    node = TabularTextPatternByVarColumns(test_data, divider='  ', columns_count=3)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_single_space_divider_ex1():
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

    node = TabularTextPatternByVarColumns(test_data, divider=' ', columns_count=2)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_single_space_divider_ex2():
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

    node = TabularTextPatternByVarColumns(test_data, divider=' ', columns_count=3)
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_custom_header_data_ex1():
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

    node = TabularTextPatternByVarColumns(test_data, columns_count=2,
                                          custom_headers_data='---------------------- ---------------')
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_tabular_custom_header_data_ex2():
    (
        dedent("""
            fruits    meat      drinks
            orange    pork      water
            peach               pepsi soda
        """).strip(),
        3,
        '--------- --------- -----------',
        [
            {'col0': 'fruits', 'col1': 'meat', 'col2': 'drinks'},
            {'col0': 'orange', 'col1': 'pork', 'col2': 'water'},
            {'col0': 'peach', 'col1': '', 'col2': 'pepsi soda'}
        ],
        dedent("""
            +--------+------+------------+
            | col0   | col1 | col2       |
            +--------+------+------------+
            | fruits | meat | drinks     |
            | orange | pork | water      |
            | peach  |      | pepsi soda |
            +--------+------+------------+
        """).strip()
    ),
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

    node = TabularTextPatternByVarColumns(test_data, columns_count=3,
                                          custom_headers_data='--------- --------- ----------')
    table = node.parse_table()
    assert table

    lst_of_dict = table.to_list_of_dict()
    assert lst_of_dict == expected_result

    tabular_txt = get_data_as_tabular(lst_of_dict)
    assert tabular_txt == expected_result_as_tabular_text


def test_to_template_snippet_ex1():
    test_data = """
LastWriteTime          Name
9/1/2021 6:13:50 AM    reference
10/5/2021 9:13:50 PM   dsc
11/2/2021 11:58:45 PM  README.md
12/16/2021 12:30:59 PM CONTRIBUTING.md
    """.strip()

    expected_template_snippet = """
LastWriteTime          Name
start() mixed_word(var_lastwritetime, at_most_2_phrase_occurrences)  mixed_word(var_name) end() -> record
    """.strip()

    expected_template = r"""
################################################################################
# Template is generated by template Community Edition
# Created date: YYYY-mm-dd
################################################################################
Value lastwritetime ([\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*( [\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*){,2})
Value name ([\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)

Start
  ^LastWriteTime +Name
  ^${lastwritetime} +${name}$$ -> Record
    """.strip()

    expected_result = [
        {'lastwritetime': '9/1/2021 6:13:50 AM', 'name': 'reference'},
        {'lastwritetime': '10/5/2021 9:13:50 PM', 'name': 'dsc'},
        {'lastwritetime': '11/2/2021 11:58:45 PM', 'name': 'README.md'},
        {'lastwritetime': '12/16/2021 12:30:59 PM', 'name': 'CONTRIBUTING.md'}
    ]

    node = TabularTextPatternByVarColumns(
        test_data, divider='  ', columns_count=2, headers_data='LastWriteTime          Name'
    )
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_template_snippet

    template = get_textfsm_template(tmpl_snippet)
    template = re.sub(r'date: \d{4}-\d\d-\d\d', 'date: YYYY-mm-dd', template)
    assert template == expected_template

    is_verified = verify(tmpl_snippet, test_data, expected_result=expected_result)
    assert is_verified


def test_to_template_snippet_ex2():
    test_data = """
fruits    meat      drinks
------    --------  -------
orange    pork      water
peach               pepsi soda
mango     chicken
    """.strip()

    expected_template_snippet = """
fruits    meat      drinks
start() letters(var_fruits)  letters(var_meat)  word(var_drinks, at_most_1_phrase_occurrences) end() -> record
start() letters(var_fruits)  letters(var_meat) end(space) -> record
start() letters(var_fruits) space(repetition_10_15) word(var_drinks, at_most_1_phrase_occurrences) end() -> record
    """.strip()

    expected_template = r"""
################################################################################
# Template is generated by template Community Edition
# Created date: YYYY-mm-dd
################################################################################
Value fruits ([a-zA-Z]+)
Value meat ([a-zA-Z]+)
Value drinks ([a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*){,1})

Start
  ^fruits +meat +drinks
  ^${fruits} +${meat} +${drinks}$$ -> Record
  ^${fruits} +${meat} *$$ -> Record
  ^${fruits}  {10,15} ${drinks}$$ -> Record
    """.strip()

    expected_result = [
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': 'pepsi', 'drinks': 'soda'},
        {'fruits': 'mango', 'meat': 'chicken', 'drinks': ''}
    ]

    node = TabularTextPatternByVarColumns(test_data)
    tmpl_snippet = node.to_template_snippet()
    assert tmpl_snippet == expected_template_snippet

    template = get_textfsm_template(tmpl_snippet)
    template = re.sub(r'date: \d{4}-\d\d-\d\d', 'date: YYYY-mm-dd', template)
    assert template == expected_template

    is_verified = verify(tmpl_snippet, test_data, expected_result=expected_result)
    assert is_verified
