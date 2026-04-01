"""
Unit tests for the `textfsmgen.engine.tabular.VarColumnTabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_to_regex.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_to_regex.py
"""


import re

from textwrap import dedent

from textfsmgen.libs import text
from textfsmgen.libs import datatype

from textfsmgen.engine.tabular import VarColumnTabularTranslator


def test_ex1():
    test_data = """
LastWriteTime          Name
9/1/2021 6:13:50 AM    reference
10/5/2021 9:13:50 PM   dsc
11/2/2021 11:58:45 PM  README.md
12/16/2021 12:30:59 PM CONTRIBUTING.md
    """.strip()

    expected_pattern = r'(?P<lastwritetime>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*){,2}) +(?P<name>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)' # noqa

    expected_results = [
        {'lastwritetime': 'LastWriteTime', 'name': 'Name'},
        {'lastwritetime': '9/1/2021 6:13:50 AM', 'name': 'reference'},
        {'lastwritetime': '10/5/2021 9:13:50 PM', 'name': 'dsc'},
        {'lastwritetime': '11/2/2021 11:58:45 PM', 'name': 'README.md'},
        {'lastwritetime': '12/16/2021 12:30:59 PM', 'name': 'CONTRIBUTING.md'}
    ]
    node = VarColumnTabularTranslator(test_data, column_count=2, column_divider='  ')
    pattern = node.to_regex()
    assert pattern == expected_pattern
    for index, line in enumerate(text.get_list_of_lines(test_data)):
        expected_result = expected_results[index]
        match = re.match(pattern, line)
        if match:
            lst_of_dict = datatype.clean_list_of_dicts([match.groupdict()])
            result = lst_of_dict.pop()
            assert result == expected_result
        else:
            assert False, 'Failed to match this line: %r' % line


def test_ex2():
    test_data = """
fruits    meat      drinks
orange    pork      water
peach               pepsi soda
    """.strip()

    expected_pattern = r'(?P<fruits>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*) (?P<meat>( {10,15})|( *[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]* *)) (?P<drinks>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)*)'  # noqa

    expected_results = [
        {'fruits': 'fruits', 'meat': 'meat', 'drinks': 'drinks'},
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'},
    ]

    node = VarColumnTabularTranslator(test_data, column_count=3, column_divider='  ')
    pattern = node.to_regex()
    assert pattern == expected_pattern
    for index, line in enumerate(text.get_list_of_lines(test_data)):
        expected_result = expected_results[index]
        match = re.match(pattern, line)
        if match:
            lst_of_dict = datatype.clean_list_of_dicts([match.groupdict()])
            result = lst_of_dict.pop()
            assert result == expected_result
        else:
            assert False, 'Failed to match this line: %r' % line

