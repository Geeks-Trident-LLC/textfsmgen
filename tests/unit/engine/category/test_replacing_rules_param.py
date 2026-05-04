"""
Unit tests for the `textfsmgen.engine.category.CategoryLinesTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/category/test_replacing_rules_param.py
    or
    $ python -m pytest tests/unit/engine/category/test_replacing_rules_param.py
"""

from textfsmgen.engine.category import CategoryLinesTranslator

test_data = "Size: 170        \tBlocks: 8          IO Block: 4096   regular file"

expected = (
    "Size: digits(var_size)wss()Blocks: digits(var_blocks)  "
    "IO Block: digits(var_io_block)  words(var_file_type)"
)


def test_yaml_list_of_pairs():
    """YAML string defining a list of [old, new] replacement pairs."""
    rules = (
        "- - mixed_word_group(var_io_block)\n"
        "  - digits(var_io_block)  words(var_file_type)\n"
    )
    node = CategoryLinesTranslator(test_data, count=3, replacing_rules=rules)
    assert node.to_template_snippet() == expected


def test_yaml_dict_of_pairs():
    """YAML string defining a dict with {curr, new} replacement entries."""
    rules = (
        "- curr: mixed_word_group(var_io_block)\n"
        "  new: digits(var_io_block)  words(var_file_type)\n"
    )
    node = CategoryLinesTranslator(test_data, count=3, replacing_rules=rules)
    assert node.to_template_snippet() == expected


def test_list_of_pairs():
    """Python list of [old, new] replacement pairs."""
    rules = [
        [
            "mixed_word_group(var_io_block)",
            "digits(var_io_block)  words(var_file_type)",
        ]
    ]
    node = CategoryLinesTranslator(test_data, count=3, replacing_rules=rules)
    assert node.to_template_snippet() == expected


def test_list_of_dict_pairs():
    """Python list of dicts containing {'curr': old, 'new': new} mappings."""
    rules = [
        {
            "curr": "mixed_word_group(var_io_block)",
            "new": "digits(var_io_block)  words(var_file_type)",
        }
    ]
    node = CategoryLinesTranslator(test_data, count=3, replacing_rules=rules)
    assert node.to_template_snippet() == expected
