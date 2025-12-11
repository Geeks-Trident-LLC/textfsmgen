import re

import pytest           # noqa

from genericlib import Misc
from genericlib import MiscObject

from textfsmgenerator.gptabular import TabularTextPatternByVarColumns


def test_to_regex_ex1():
    test_data = """
LastWriteTime          Name
9/1/2021 6:13:50 AM    reference
10/5/2021 9:13:50 PM   dsc
11/2/2021 11:58:45 PM  README.md
12/16/2021 12:30:59 PM CONTRIBUTING.md
    """.strip()

    expected_pattern = r'(?P<lastwritetime>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*( [\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*){,2}) +(?P<name>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)' # noqa

    expected_results = [
        {'lastwritetime': 'LastWriteTime', 'name': 'Name'},
        {'lastwritetime': '9/1/2021 6:13:50 AM', 'name': 'reference'},
        {'lastwritetime': '10/5/2021 9:13:50 PM', 'name': 'dsc'},
        {'lastwritetime': '11/2/2021 11:58:45 PM', 'name': 'README.md'},
        {'lastwritetime': '12/16/2021 12:30:59 PM', 'name': 'CONTRIBUTING.md'}
    ]

    node = TabularTextPatternByVarColumns(test_data, columns_count=2, divider='  ')
    pattern = node.to_regex()
    assert pattern == expected_pattern
    for index, line in enumerate(Misc.get_list_of_lines(test_data)):
        expected_result = expected_results[index]
        match = re.match(pattern, line)
        if match:
            lst_of_dict = MiscObject.cleanup_list_of_dict([match.groupdict()])
            result = lst_of_dict.pop()
            assert result == expected_result
        else:
            assert False, 'Failed to match this line: %r' % line


def test_to_regex_ex2():
    test_data = """
fruits    meat      drinks
orange    pork      water
peach               pepsi soda
    """.strip()

    expected_pattern = r'(?P<fruits>[a-zA-Z]+) (?P<meat>( {10,15})|( *[a-zA-Z]+ *)) (?P<drinks>[a-zA-Z][a-zA-Z0-9]*( [a-zA-Z][a-zA-Z0-9]*){,1})'  # noqa

    expected_results = [
        {'fruits': 'fruits', 'meat': 'meat', 'drinks': 'drinks'},
        {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'},
        {'fruits': 'peach', 'meat': '', 'drinks': 'pepsi soda'},
    ]

    node = TabularTextPatternByVarColumns(test_data, columns_count=3, divider='  ')
    pattern = node.to_regex()
    assert pattern == expected_pattern
    for index, line in enumerate(Misc.get_list_of_lines(test_data)):
        expected_result = expected_results[index]
        match = re.match(pattern, line)
        if match:
            lst_of_dict = MiscObject.cleanup_list_of_dict([match.groupdict()])
            result = lst_of_dict.pop()
            assert result == expected_result
        else:
            assert False, 'Failed to match this line: %r' % line
