"""
Unit tests for the `textfsmgen.core.LineParser` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/core/test_parsed_line_class.py
    or
    $ python -m pytest tests/unit/core/test_parsed_line_class.py
"""

import pytest

from textfsmgen.core.template import LineParser


@pytest.mark.parametrize(
    "line, expected",
    [
        ("", True),  # empty string
        ("   \t\n", True),  # whitespace only
        ("hello", False),  # non-empty string
        ("   hello   ", False),  # string with leading and trailing
    ],
)
def test_is_empty(line, expected):
    """Unit tests for the `LineParser.is_empty` property."""
    parsed_line = LineParser(line)
    assert parsed_line.is_empty is expected


@pytest.mark.parametrize(
    "line, expected",
    [
        ("hello", True),  # simple word
        ("Hello", True),  # capitalized word
        ("HELLO", True),  # uppercase word
        ("hello123", True),  # alphanumeric word
        ("hello_world", True),  # underscore inside word
        ("hello world", False),  # multiple words
        ("_hello", False),  # leading underscore not allowed
        ("hello-world", False),  # hyphen not matched by \w
        ("123", False),  # digits only
        ("", False),  # empty string
        ("   ", False),  # whitespace only
    ],
)
def test_is_a_word(line, expected):
    """Unit tests for the `LineParser.is_a_word` property."""
    parsed_line = LineParser(line)
    assert parsed_line.is_word is expected


@pytest.mark.parametrize(
    "line, expected",
    [
        ("!!!", True),  # symbols only
        ("", False),  # empty string excluded
        ("   ", False),  # whitespace only
        ("abc123", False),  # letters + digits
        ("hello!", False),  # letters + symbols
        ("abc", False),  # letters only
        ("12345", False),  # digits only
    ],
)
def test_is_not_containing_letter(line, expected):
    """Unit tests for the `LineParser.is_not_containing_letter` property."""
    parsed_line = LineParser(line)
    assert parsed_line.no_letters is expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            "",  # line
            "",  # expected
        ),
        (
            "  ",  # line
            "",  # expected
        ),
        (
            "Start",  # line
            "Start",  # expected
        ),
        (
            "===   ==========   ======",  # line
            "  ^={2,} +={2,} +={2,}",  # expected
        ),
        (
            "===   ==========   ====== end()",  # line
            "  ^={2,} +={2,} +={2,}$$",  # expected
        ),
        (
            "temp is digits(var_degree) celsius.",  # line
            "  ^temp is ${degree} celsius\\.",  # expected
        ),
        (
            "temp is digits(var_degree) word(var_unit).",  # line
            "  ^temp is ${degree} ${unit}\\.",  # expected
        ),
        (
            "temp is digits(var_degree) word(var_unit). -> Record",  # line
            "  ^temp is ${degree} ${unit}\\. -> Record",  # expected
        ),
        (
            "temp is digits(var_degree, meta_data_Filldown) word(var_unit). -> Record",
            "  ^temp is ${degree} ${unit}\\. -> Record",
        ),
        (
            "temp is digits(var_degree) word(var_unit). -> Record",  # line
            "  ^temp is ${degree} ${unit}\\. -> Record",  # expected
        ),
    ],
)
def test_get_statement(line, expected):
    """
    Verify that `LineParser.get_statement` generates normalized template statements.
    """
    parsed_line = LineParser(line)
    statement = parsed_line.statement()
    assert statement == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        # comment__ flag
        (
            "comment__ temp $5 dollars",  # line
            "  # temp $5 dollars",  # expected
        ),
        # keep__ flag
        (
            "keep__ # temp $5 dollars",  # line
            "  ^# temp $5 dollars",  # expected
        ),
        # ignore_case__ flag
        (
            "ignore_case__ temp is digits(var_degree) celsius.",  # line
            "  ^(?i)temp is ${degree} celsius\\.",  # expected
        ),
    ],
)
def test_get_statement_with_flag(line, expected):
    """
    Verify that `LineParser.get_statement` correctly interprets flag directives.

    This test ensures that special flags (`comment__`, `keep__`, `ignore_case__`)
    applied to input lines are properly converted into normalized TextFSM
    template statements.
    """
    parsed_line = LineParser(line)
    statement = parsed_line.statement()
    assert statement == expected


@pytest.mark.parametrize(
    ("line", "expected", "template_op"),
    [
        (
            "temp is digits(var_degree)",  # line
            "  ^temp is ${degree}",  # expected
            "",  # template_op == ""
        ),
        # Right op: Record, NoRecord, Clear, or ClearAll
        (
            "temp is digits(var_degree)  ->    record",  # line
            "  ^temp is ${degree} -> Record",  # expected
            "Record",  # template_op == "Record"
        ),
        (
            "temp is digits(var_degree) -> norecord",  # line
            "  ^temp is ${degree} -> NoRecord",  # expected
            "NoRecord",  # template_op == "NoRecord"
        ),
        (
            "temp is digits(var_degree) -> clear",  # line
            "  ^temp is ${degree} -> Clear",  # expected
            "Clear",  # template_op == "Clear"
        ),
        (
            "temp is digits(var_degree) -> clearall",  # line
            "  ^temp is ${degree} -> ClearAll",  # expected
            "ClearAll",  # template_op == "ClearAll"
        ),
        # left op: Next, Continue, or Error
        (
            "temp is digits(var_degree) -> next",  # line
            "  ^temp is ${degree} -> Next",  # expected
            "Next",  # template_op == "Next"
        ),
        (
            "temp is digits(var_degree) -> continue",  # line
            "  ^temp is ${degree} -> Continue",  # expected
            "Continue",  # template_op == "Continue"
        ),
        (
            "temp is digits(var_degree) -> error",  # line
            "  ^temp is ${degree} -> Error",  # expected
            "Error",  # template_op == "Error"
        ),
        # combining left op + right op: Continue.Record, Next.Record
        (
            "temp is digits(var_degree) -> next.record",  # line
            "  ^temp is ${degree} -> Next.Record",  # expected
            "Next.Record",  # template_op == "Next.Record"
        ),
        (
            "temp is digits(var_degree) -> continue.record",  # line
            "  ^temp is ${degree} -> Continue.Record",  # expected
            "Continue.Record",  # template_op == "Continue.Record"
        ),
    ],
)
def test_get_statement_with_textfsm_op(line, expected, template_op):
    """
    Verify that `LineParser.get_statement` correctly interprets TextFSM template operators.

    This test ensures that user data lines containing template operators
    (e.g., `Record`, `NoRecord`, `Clear`, `Next`, `Continue`, `Error`)
    are normalized into valid TextFSM statements and that the operator
    is stored in the `template_op` attribute.

    """
    parsed_line = LineParser(line)
    statement = parsed_line.statement()
    assert statement == expected
    assert parsed_line.template_op == template_op


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (
            "temp is digits(var_degree, meta_data_Filldown). -> Record",
            "  ^temp is ${degree}\\. -> Record",
        ),
        (
            "temp is digits(var_degree, meta_data_Fillup). -> Record",
            "  ^temp is ${degree}\\. -> Record",
        ),
        (
            "temp is digits(var_degree, meta_data_Key). -> Record",
            "  ^temp is ${degree}\\. -> Record",
        ),
        (
            "temp is digits(var_degree, meta_data_List). -> Record",
            "  ^temp is ${degree}\\. -> Record",
        ),
        (
            "temp is digits(var_degree, meta_data_Required). -> Record",
            "  ^temp is ${degree}\\. -> Record",
        ),
        (
            "temp is digits(var_degree, meta_data_Required_Filldown). -> Record",
            "  ^temp is ${degree}\\. -> Record",
        ),
    ],
)
def test_get_statement_that_understand_textfsm_option(line, expected):
    """
    Verify that `LineParser.get_statement` correctly interprets TextFSM metadata options.

    This test ensures that variable definitions containing metadata flags
    (e.g., `Filldown`, `Fillup`, `Key`, `List`, `Required`) are normalized
    into valid TextFSM template statements. The metadata is recognized but
    does not alter the final regex pattern in the generated statement.

    """
    parsed_line = LineParser(line)
    statement = parsed_line.statement()
    assert statement == expected
