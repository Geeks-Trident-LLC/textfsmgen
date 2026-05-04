"""
Unit tests for the `textfsmgen.engine.tabular.VarColumnTabularTranslator` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/tabular/test_custom_header.py
    or
    $ python -m pytest tests/unit/engine/tabular/test_custom_header.py
"""

from textwrap import dedent

from textfsmgen.engine.tabular import VarColumnTabularTranslator

from textfsmgen.core.verify import verify


def test_parses_rows_with_full_cells_per_column():
    test_data = dedent("""
        LastWriteTime          Name
        ---------------------- -------------------
        9/1/2021 6:13:50 AM    reference
        10/5/2021 9:13:50 PM   dsc
        11/2/2021 11:58:45 PM  README.md
        12/16/2021 12:30:59 PM CONTRIBUTING.md
                """).strip()

    exp_snippet = dedent("""
        LastWriteTime          Name
        start() 3_mixed_word(var_lastwritetime)  mixed_word(var_name) end() -> record
    """).strip()

    expected_result = [
        {"lastwritetime": "9/1/2021 6:13:50 AM", "name": "reference"},
        {"lastwritetime": "10/5/2021 9:13:50 PM", "name": "dsc"},
        {"lastwritetime": "11/2/2021 11:58:45 PM", "name": "README.md"},
        {"lastwritetime": "12/16/2021 12:30:59 PM", "name": "CONTRIBUTING.md"},
    ]

    translator = VarColumnTabularTranslator(
        test_data,
        column_count=2,
        custom_header_text="---------------------- -------------------",
        has_header_row=True,
    )
    table = translator.parse_table()
    assert table

    snippet = table.to_snippet()
    assert snippet == exp_snippet

    ok = verify(snippet, test_data, expected_result=expected_result)
    assert ok


def test_parses_row_with_empty_cell():

    test_data = dedent("""
        fruits    meat      drinks
        orange    pork      water
        peach               pepsi soda
                """).strip()

    exp_snippet = dedent("""
        fruits    meat      drinks
        start() word(var_fruits)  word(var_meat)  words(var_drinks) end() -> record
        start() word(var_fruits) 10_15_space() words(var_drinks) end() -> record
    """).strip()

    expected_result = [
        {"fruits": "orange", "meat": "pork", "drinks": "water"},
        {"fruits": "peach", "meat": "", "drinks": "pepsi soda"},
    ]

    translator = VarColumnTabularTranslator(
        test_data,
        column_count=3,
        custom_header_text="--------- --------- ----------",
        has_header_row=True,
    )
    table = translator.parse_table()
    assert table

    snippet = table.to_snippet()
    assert snippet == exp_snippet

    adjust_snippet = snippet.replace(
        "  word(var_meat)  ", "1_8_space()word(var_meat)1_8_space()"
    )

    ok = verify(adjust_snippet, test_data, expected_result=expected_result)
    assert ok
