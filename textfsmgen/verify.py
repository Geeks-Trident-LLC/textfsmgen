"""
textfsmgen.verify
=================

Validation utilities for TextFSM Generator.

This module provides helper functions to verify templates, inputs,
and parsing results used within the TextFSM Generator framework.
It ensures that generated templates and data structures conform
to expected formats, improving reliability and maintainability.
"""


from textfsmgen import TemplateBuilder


def verify(
    template_snippet: str,
    test_data: str,
    expected_rows_count: int | None = None,
    expected_result: list[dict] | None = None,
    ignore_space: bool = True,
) -> bool:
    """
    Verify a TextFSM template against test data.

    This function creates a `TemplateBuilder` instance using the provided
    template snippet and test data, then validates the parsed output against
    optional expectations such as row count and expected results.

    Parameters
    ----------
    template_snippet : str
        Raw user data snippet to be converted into a TextFSM template.
    test_data : str
        Input text data to be parsed by the template.
    expected_rows_count : int, optional
        Expected number of parsed rows. If provided, the actual row count
        is compared against this value.
    expected_result : list of dict, optional
        Expected parsed result. If provided, the actual parsed rows are
        compared against this list of dictionaries.
    ignore_space : bool, default=True
        If True, strip leading and trailing spaces from parsed data before
        comparison.

    Returns
    -------
    bool
        True if verification succeeds, False otherwise.

    Raises
    ------
    TemplateBuilderError
        Raised if an exception occurs during parsing or verification.
    TemplateBuilderInvalidFormat
        Raised if the provided snippet has an invalid format.
    """
    builder = TemplateBuilder(user_data=template_snippet, test_data=test_data)
    is_verified = builder.verify(
        expected_rows_count=expected_rows_count,
        expected_result=expected_result,
        ignore_space=ignore_space,
    )
    return is_verified
