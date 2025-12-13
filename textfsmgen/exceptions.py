"""Exception classes for the TextFSM Generator.

This module defines custom exceptions used throughout the TextFSM
Generator library to handle template parsing, building, and validation
errors in a structured way.
"""


class TemplateError(Exception):
    """
    Base class for all template-related errors in the TextFSM Generator.

    Raised when a general error occurs during template construction
    or processing.
    """


class TemplateParsedLineError(TemplateError):
    """
    Raised when a parsed line cannot be processed correctly
    by the template builder.

    This typically indicates invalid syntax or an unsupported format
    within a template line.
    """


class TemplateBuilderError(TemplateError):
    """
    Raised when an error occurs during template building.

    Serves as a general-purpose exception for builder failures.
    """


class TemplateBuilderInvalidFormat(TemplateError):
    """
    Raised when user-provided data has an invalid format
    during template building.
    """


class NoUserTemplateSnippetError(TemplateError):
    """
    Raised when user-provided template data is empty or missing.
    """


class NoTestDataError(TemplateError):
    """
    Raised when no test data is available for validation
    or execution of a template.
    """
