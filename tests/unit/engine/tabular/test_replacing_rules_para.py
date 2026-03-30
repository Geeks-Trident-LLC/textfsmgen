"""
Unit tests for the `textfsmgen.engine.category.TabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_replacing_rules_para.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_replacing_rules_para.py
"""
from textfsmgen.engine.tabular import TabularTranslator

test_data = (
    "drwxr-xr-x 1 user1 197609       0 Dec 19 15:49 ./\n"
    "-rw-r--r-- 1 user1 197609   18765 Nov 17 18:43 LICENSE.txt"
)

expected = (
    "start() mixed_word(var_fperm)  digits(var_links)  word(var_uname)  "
    "digits(var_gid)  digits(var_fsize)  3_mixed_word(var_datatime)  "
    "non_wss(var_fpath) end() -> record"
)


def test_yaml_list_of_pairs():
    """YAML string defining a list of [old, new] replacement pairs."""
    rules = """
- - letters(var_month)  digits(var_date)  mixed_number(var_time)
  - 3_mixed_word(var_datatime)
    """
    node = TabularTranslator(
        test_data,
        column_divider=" ",
        column_count=9,
        headers="fperm, links, uname, gid, fsize, month, date, time, fpath",
        has_header_row=False,
        replacing_rules=rules
    )
    assert node.to_template_snippet() == expected


def test_yaml_dict_of_pairs():
    """YAML string defining a dict with {curr, new} replacement entries."""
    rules = """
- curr: letters(var_month)  digits(var_date)  mixed_number(var_time)
  new: 3_mixed_word(var_datatime)
    """
    node = TabularTranslator(
        test_data,
        column_divider=" ",
        column_count=9,
        headers="fperm, links, uname, gid, fsize, month, date, time, fpath",
        has_header_row=False,
        replacing_rules=rules
    )
    assert node.to_template_snippet() == expected


def test_list_of_pairs():
    """Python list of [old, new] replacement pairs."""
    rules = [
        [
            "letters(var_month)  digits(var_date)  mixed_number(var_time)",
            "3_mixed_word(var_datatime)",
        ]
    ]
    node = TabularTranslator(
        test_data,
        column_divider=" ",
        column_count=9,
        headers="fperm, links, uname, gid, fsize, month, date, time, fpath",
        has_header_row=False,
        replacing_rules=rules
    )
    assert node.to_template_snippet() == expected


def test_list_of_dict_pairs():
    """Python list of dicts containing {'curr': old, 'new': new} mappings."""
    rules = [
        {
            "curr": "letters(var_month)  digits(var_date)  mixed_number(var_time)",
            "new": "3_mixed_word(var_datatime)",
        }
    ]
    node = TabularTranslator(
        test_data,
        column_divider=" ",
        column_count=9,
        headers="fperm, links, uname, gid, fsize, month, date, time, fpath",
        has_header_row=False,
        replacing_rules=rules
    )
    assert node.to_template_snippet() == expected
