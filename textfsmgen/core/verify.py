"""
textfsmgen.core.verify
======================

Validation utilities for TextFSM Generator.

This module provides helper functions to verify templates, inputs,
and parsing results used within the TextFSM Generator framework.
It ensures that generated templates and data structures conform
to expected formats, improving reliability and maintainability.
"""

from typing import Optional
import traceback
import json

from io import StringIO
from textfsm import TextFSM

from textfsmgen.libs.text import decorate_text
from textfsmgen.libs import datatype

from textfsmgen import TemplateBuilder
from textfsmgen.libs.generic import StatusString


def verify_snippet(
    template_snippet: str,
    test_data: str,
    expected_rows_count: Optional[int] = None,
    expected_result: Optional[list[dict]] = None,
    ignore_space: bool = True,
    debug: bool = False,
) -> StatusString:
    """
    Verify a template snippet against test data.
    """
    builder = TemplateBuilder(user_data=template_snippet, test_data=test_data)
    status = builder.verify(
        expected_rows_count=expected_rows_count,
        expected_result=expected_result,
        ignore_space=ignore_space,
        debug=debug,
    )
    return status


def verify_textfsm(
    textfsm_template: str,
    test_data: str,
    expected_rows_count: Optional[int] = None,
    expected_result: Optional[list[dict]] = None,
    ignore_space: bool = True,
    debug: bool = False,
) -> StatusString:
    """Verify a template snippet against test data."""

    # ---------------------------------------------------------------------
    def update_and_print(items, data, subject="", append_newline=True):
        if subject:
            txt = decorate_text(f"{subject:<16}")
            items.append(txt)
            print(txt)
        new_data = f"{data}\n" if append_newline else data
        items.append(new_data)
        print(new_data)

    # ---------------------------------------------------------------------

    template = textfsm_template.strip()

    if not template:
        if debug:
            print("Empty template.")
        return StatusString("Empty template", status=False)

    if not test_data:
        if debug:
            print("Empty test data.")
        return StatusString("Empty test data", status=False)

    try:
        stream = StringIO(template)
        parser = TextFSM(stream)
        rows = parser.ParseTextToDicts(test_data)
    except Exception as ex:
        title = decorate_text(f"{type(ex).__name__}: {ex}")
        error = traceback.format_exc()
        raise Exception(f"{title}\n{error}")

    if not rows:
        if debug:
            print("There is no record after parsed.")
        return StatusString("There is no record after parsed.", status=False)

    verified_msg = ""
    is_verified = True

    # Validate row count
    if expected_rows_count is not None:
        actual_count = len(rows)
        chk = expected_rows_count == actual_count

        is_verified = is_verified and chk
        verified_msg = (
            f"Parsed-row-count and expected-row-count are {expected_rows_count}."
            if chk
            else f"Parsed-row-count is {actual_count} while expected-row-count is {expected_rows_count}."
        )

    # Validate expected result
    if expected_result is not None:
        rows_to_compare = datatype.clean_list_of_dicts(rows) if ignore_space else rows
        chk = rows_to_compare == expected_result
        is_verified = is_verified and chk
        msg = (
            "Parsed result and expected result are matched."
            if chk
            else "Parsed result and expected result are different."
        )
        verified_msg = f"{verified_msg}\n{msg}"

    # Default success message
    if is_verified:
        verified_msg = f"{verified_msg}\nParsed result has record(s)."

    verified_msg = verified_msg.strip()
    # Debug output
    if debug:
        parts = []
        # Template
        update_and_print(parts, template, subject="Template:")
        # Test Data
        update_and_print(parts, test_data, subject="Test Data:")
        # Expected Result
        if expected_result is not None:
            update_and_print(parts, expected_result, subject="Expected Result:")

        # Test Result
        if rows is not None:
            rows_to_compare = (
                datatype.clean_list_of_dicts(rows) if ignore_space else rows
            )
            formatted_result = json.dumps(rows_to_compare, indent=2)
            update_and_print(parts, formatted_result, subject="Test Result:")

        verified_msg = f"Verified Message: {verified_msg}"
        update_and_print(parts, verified_msg, append_newline=False)
        report = "\n".join(parts)
        print(report)
        return StatusString(report, status=is_verified)
    return StatusString(verified_msg, status=is_verified)
