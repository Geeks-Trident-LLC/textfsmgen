"""
textfsmgen.exceptions
=====================

Custom exception classes for the TextFSM Generator library.

"""

from typing import Type, Optional


class PatternError(Exception):
    """Base exception for errors encountered during pattern conversion."""


class EscapePatternError(PatternError):
    """Raised when an error occurs while performing soft regex escaping."""


class PatternReferenceError(PatternError):
    """Raised when a PatternRegistry instance fails or is invalid."""


class TextPatternError(Exception):
    """Raised when text-based pattern conversion fails."""


class ElementPatternError(Exception):
    """Raised when element-level pattern conversion fails."""


class LinePatternError(PatternError):
    """Raised when line-based pattern conversion fails."""


class LineError(Exception):
    """Base exception for errors raised by the `text.Line` class."""


class LineArgumentError(LineError):
    """Exception raised when invalid arguments are provided to `text.Line`."""


class InvalidExceptionType(Exception):
    """Raised when an invalid exception type is encountered."""


class TemplateError(Exception):  # noqa
    """
    Base class for all template-related errors in the TextFSM Generator.

    Raised when a general error occurs during template construction
    or processing.
    """


class TemplateParsedLineError(TemplateError):
    """
    Raised when a parsed line cannot be processed correctly
    by the template builder.
    """


class TemplateBuilderError(TemplateError):
    """Raised when an error occurs during template building."""


class TemplateBuilderInvalidFormat(TemplateError):
    """
    Raised when user-provided data has an invalid format
    during template building.
    """


class NoUserTemplateSnippetError(TemplateError):
    """Raised when user-provided template data is empty or missing."""


class NoTestDataError(TemplateError):
    """
    Raised when no test data is available for validation
    or execution of a template.
    """


def raise_exception(
        ex: Exception,
        cls: Optional[Type[Exception]] = None,
        fmt: str = "{} - {}",
        msg: str = "",
        is_skipped: bool = False,
):
    """
    Raise a formatted exception or skip raising.
    """

    if not is_skipped:
        fmt = str(fmt)

        if not isinstance(ex, Exception):  # if ex is NOT instance of Exception
            ex_type_name = ex.__name__ if isinstance(ex, type) else type(
                ex).__name__
            failure = (
                f"Invalid argument: expected an Exception instance, got {ex_type_name}."
            )
            raise InvalidExceptionType(failure)

        # Determine which exception class to use

        is_cls_exception = isinstance(cls, type) and issubclass(cls, Exception)
        exception_cls = cls if is_cls_exception else type(ex)
        if msg:
            raise exception_cls(msg)
        try:
            ex_name = type(ex).__name__
            failure = fmt.format(ex_name, ex)
            raise exception_cls(failure)
        except Exception as other_ex:
            other_failure = f"{type(other_ex).__name__} - {other_ex}"
            raise other_ex.__class__(other_failure)


def create_runtime_error(obj=None, msg=""):
    """
    Dynamically create a custom runtime exception instance.
    """
    if obj is None:
        exc_cls_name = "RuntimeError"
    else:
        exc_cls_name = obj if isinstance(obj,
                                         str) else f"{type(obj).__name__}RTError"

    # Normalize class name: ensure first character is uppercase
    exc_cls_name = str(exc_cls_name)
    exc_cls_name = exc_cls_name[0].upper() + exc_cls_name[1:]

    exc_cls = type(exc_cls_name, (Exception,), {})
    return exc_cls(msg)


def raise_runtime_error(obj=None, msg=""):
    """
    Raise a dynamically created runtime exception.
    """
    exc_obj = create_runtime_error(obj=obj, msg=msg)
    raise exc_obj
