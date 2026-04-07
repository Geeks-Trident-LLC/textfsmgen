"""
Unit tests for the `textfsmgen.exceptions.RuntimeException` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/test_exceptions.py
    or
    $ python -m pytest tests/unit/test_exceptions.py
"""

import pytest   # noqa

from textfsmgen.exceptions import RuntimeException

from tests.unit import DummyClass


class TestRuntimeException:
    """
    Unit tests for `RuntimeException`.

    Coverage:
    - Instance method `raise_runtime_error` with string, object, and empty name.
    - Class method `do_raise_runtime_error` with None, string, and object inputs.
    - Ensures correct exception class names and messages are raised.
    """

    def test_instance_raise_with_string_name(self):
        """
        Verify that `raise_runtime_error` raises a custom exception when
        given a string name.

        Scenario:
        - Call `raise_runtime_error("CustomError", "something went wrong")`
          on a `RuntimeException` instance.

        Assertions:
        - The raised exception class is named "CustomError".
        - The exception message equals "something went wrong".
        """
        runtime_exc = RuntimeException()
        with pytest.raises(Exception) as exc_info:
            runtime_exc.raise_runtime_error("CustomError", "something went wrong")
        exc = exc_info.value
        assert exc.__class__.__name__ == "CustomError"
        assert str(exc) == "something went wrong"

    def test_instance_raise_with_empty_name_uses_self(self):
        """
        Verify that `raise_runtime_error` derives the exception class name
        from the instance when no name is provided.

        Scenario:
        - Call `raise_runtime_error("", "failure from self")` on a `RuntimeException` instance.

        Assertions:
        - The raised exception class name is "RuntimeExceptionRTError".
        - The exception message equals "failure from self".
        """
        runtime_exc = RuntimeException()
        with pytest.raises(Exception) as exc_info:
            runtime_exc.raise_runtime_error("", "failure from self")
        exc = exc_info.value
        # Class name derived from RuntimeException → RuntimeExceptionRTError
        assert exc.__class__.__name__ == "RuntimeExceptionRTError"
        assert str(exc) == "failure from self"

    def test_class_method_raise_with_none_defaults_to_runtime_error(self):
        """
        Verify that `do_raise_runtime_error` defaults to `RuntimeError` when `obj` is None.

        Scenario:
        - Call `do_raise_runtime_error(None, "generic failure")`.

        Assertions:
        - The raised exception class name is "RuntimeError".
        - The exception message equals "generic failure".
        """
        with pytest.raises(Exception) as exc_info:
            RuntimeException.do_raise_runtime_error(None, "generic failure")
        exc = exc_info.value
        assert exc.__class__.__name__ == "RuntimeError"
        assert str(exc) == "generic failure"

    def test_class_method_raise_with_string(self):
        """
        Verify that `do_raise_runtime_error` raises a custom exception when
        given a string name.

        Scenario:
        - Call `do_raise_runtime_error("AnotherError", "bad input")`.

        Assertions:
        - The raised exception class name is "AnotherError".
        - The exception message equals "bad input".
        """
        with pytest.raises(Exception) as exc_info:
            RuntimeException.do_raise_runtime_error("AnotherError", "bad input")
        exc = exc_info.value
        assert exc.__class__.__name__ == "AnotherError"
        assert str(exc) == "bad input"

    def test_class_method_raise_with_object(self):
        """
        Verify that `do_raise_runtime_error` derives the exception class name
        from an object.

        Scenario:
        - Call `do_raise_runtime_error(obj, "dummy failure")` where `obj` is
          an instance of `DummyClass`.

        Assertions:
        - The raised exception class name is "DummyClassRTError".
        - The exception message equals "dummy failure".
        """
        obj = DummyClass()
        with pytest.raises(Exception) as exc_info:
            RuntimeException.do_raise_runtime_error(obj, "dummy failure")
        exc = exc_info.value
        assert exc.__class__.__name__ == "DummyClassRTError"
        assert str(exc) == "dummy failure"