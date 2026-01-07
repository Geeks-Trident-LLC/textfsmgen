"""
textfsmgen.exceptions
=====================

Custom exception classes for the TextFSM Generator library.

This module defines application‑specific exceptions that provide
clearer error reporting and handling across the `textfsmgen` package.
By centralizing exception definitions, the library ensures consistent
messaging and easier debugging for both developers and end users.

Purpose
-------
- Provide meaningful exception types for template generation, parsing,
  and configuration errors.
- Improve error handling by distinguishing between different failure
  scenarios.
- Support GUI and CLI workflows with user‑friendly error messages.

Notes
-----
- All custom exceptions inherit from `TextFSMGenError` to allow
  consistent catching at a higher level.
- Exception messages are designed to be user‑friendly for GUI dialogs
  while still informative for developers.
"""
from genericlib.exceptions import raise_runtime_error
from genericlib.exceptions import raise_exception

raise_exception = raise_exception

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


class RuntimeException:
    """
    Utility class for raising dynamically created runtime exceptions.

    This class provides convenience methods that delegate to
    `genericlib.exceptions.raise_runtime_error` to generate and raise custom
    exception types at runtime. The exception class name is derived
    from either a provided string or the class name of an object.
    """

    def raise_runtime_error(self, name: str = "", msg: str = ""):
        """
        Raise a dynamically created runtime exception (instance method).

        Parameters
        ----------
        name : str, optional
            The name to use for the exception class. If empty, the
            instance itself is used to derive the class name.
        msg : str, optional
            The error message to associate with the raised exception.
            Defaults to an empty string.

        Raises
        ------
        Exception
            A dynamically created exception instance with the specified
            message.
        """
        name = name.strip()
        obj = name or self
        raise_runtime_error(obj=obj, msg=msg)

    @classmethod
    def do_raise_runtime_error(cls, obj=None, msg: str = ""):
        """
        Raise a dynamically created runtime exception (class method).

        Parameters
        ----------
        obj : Any, optional
            The object or string used to derive the exception class name.
            Defaults to None, which results in "RuntimeError".
        msg : str, optional
            The error message to associate with the raised exception.
            Defaults to an empty string.

        Raises
        ------
        Exception
            A dynamically created exception instance with the specified
            message.
        """
        raise_runtime_error(obj=obj, msg=msg)
