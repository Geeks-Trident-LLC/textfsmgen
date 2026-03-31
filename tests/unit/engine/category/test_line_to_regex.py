"""
Unit tests for the `textfsmgen.engine.category.CategoryLineTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/category/test_line_to_regex.py
    or
    $ python -m pytest tests/unit/engine/category/test_line_to_regex.py
"""


import re

import pytest

from textfsmgen.engine.category import CategoryLineTranslator
from textfsmgen.engine.category import VAR_REGISTRY


@pytest.mark.parametrize(
    "line, count, exp_pattern, exp_result",
    [
        (
            'fruits: orange, peach',
            1,
            r'fruits: *(?P<fruits>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+)',  # noqa
            {'fruits': 'orange, peach'}
        ),
        (
            'total   fruits: orange, peach',
            1,
            r'total +fruits: *(?P<total_fruits>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+)',     # noqa
            {'total_fruits': 'orange, peach'}
        ),
        (
            'total fruit(s): orange, peach',
            1,
            r'total fruit\(s\): *(?P<total_fruit_s>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+)',   # noqa
            {'total_fruit_s': 'orange, peach'}
        ),
        (
            'fruits: orange   meat: pork  drinks: water',
            3,
            r'fruits: *(?P<fruits>[a-zA-Z]+) +meat: *(?P<meat>[a-zA-Z]+) +drinks: *(?P<drinks>[a-zA-Z]+)',
            {'fruits': 'orange', 'meat': 'pork', 'drinks': 'water'}
        ),
        (
            'fruits:   meat: ',
            2,
            r'fruits: *(?P<fruits>.*|) +meat: *(?P<meat>.*|)',
            {'fruits': '', 'meat': ''}
        ),
        (
            'fruits:   meat:  drinks: ',
            3,
            r'fruits: *(?P<fruits>.*|) +meat: *(?P<meat>.*|) +drinks: *(?P<drinks>.*|)',
            {'fruits': '', 'meat': '', 'drinks': ''}
        ),
        (
            'fruits:   meat: pork  drinks: ',
            3,
            r'fruits: *(?P<fruits>.*|) +meat: *(?P<meat>[a-zA-Z]+) +drinks: *(?P<drinks>.*|)',
            {'fruits': '', 'meat': 'pork', 'drinks': ''}
        ),
        (
            'fruits:   meat: pork  drinks: water',
            3,
            r'fruits: *(?P<fruits>.*|) +meat: *(?P<meat>[a-zA-Z]+) +drinks: *(?P<drinks>[a-zA-Z]+)',
            {'fruits': '', 'meat': 'pork', 'drinks': 'water'}
        ),
        (
            'fruits: orange, peach  meat:   drinks: water',
            3,
            r'fruits: *(?P<fruits>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+) +meat: *(?P<meat>.*|) +drinks: *(?P<drinks>[a-zA-Z]+)',    # noqa
            {'fruits': 'orange, peach', 'meat': '', 'drinks': 'water'}
        ),
        (
            'time: 08:30:00 P.M.',
            1,
            r'time: *(?P<time>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+)',
            {'time': '08:30:00 P.M.'}
        ),
        (
            'time: 08:30:00 P.M.  mac_addr: 11:22:33:44:55:66',
            2,
            r'time: *(?P<time>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+) +mac_addr: *(?P<mac_addr>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)',     # noqa
            {'time': '08:30:00 P.M.', 'mac_addr': '11:22:33:44:55:66'}
        ),
        (
            'time: 08:30:00 P.M.   ipv6: ::1234, 2000::ab, 2000::   mac_addr: 11:22:33:44:55:66',
            3,
            r'time: *(?P<time>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+) +ipv6: *(?P<ipv6>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+) +mac_addr: *(?P<mac_addr>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)',   # noqa
            {'time': '08:30:00 P.M.', 'ipv6': '::1234, 2000::ab, 2000::', 'mac_addr': '11:22:33:44:55:66'}
        ),
    ]
)
def test(line: str, count: int, exp_pattern,exp_result):
    """
    Verify that `CategoryLineTranslator.to_regex` generates the expected regex
    pattern and correctly matches the provided line.
    """
    # --- Action ---
    VAR_REGISTRY.reset()
    node = CategoryLineTranslator(line, count=count)
    pattern = node.to_regex()

    # --- Assertions ---
    assert pattern == exp_pattern, (
        f"Generated pattern {pattern!r} does not match expected {exp_pattern!r}"
    )

    match = re.match(pattern, line)
    if not match:
        pytest.fail(
            f"No match found for line {line!r} using pattern {pattern!r}")

    result = match.groupdict()
    assert result == exp_result, (
        f"Regex groups {result} do not match expected {exp_result}"
    )