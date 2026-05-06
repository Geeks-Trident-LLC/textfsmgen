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

from textfsmgen import TemplateBuilder


def verify_snippet(
    template_snippet: str,
    test_data: str,
    expected_rows_count: Optional[int] = None,
    expected_result: Optional[list[dict]] = None,
    ignore_space: bool = True,
    debug: bool = False,
) -> bool:
    """
    Verify a template snippet against test data.
    """
    builder = TemplateBuilder(user_data=template_snippet, test_data=test_data)
    is_verified = builder.verify(
        expected_rows_count=expected_rows_count,
        expected_result=expected_result,
        ignore_space=ignore_space,
        debug=debug
    )
    return is_verified



