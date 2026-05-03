"""
Unit tests for the `textfsmgen.gp.LineData` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/translate/test_line_data_class.py
    or
    $ python -m pytest tests/unit/translate/test_line_data_class.py
"""

import pytest   # noqa

from textfsmgen.engine.line import LineData


class TestLineData:
    """Unit tests for the LineData class."""

    @pytest.mark.parametrize(
        "input_str, expected_raw, expected_data",
        [
            ("hello", "hello", "hello"),
            ("   hello   ", "   hello   ", "hello"),
            ("   \t", "   \t", ""),  # whitespace-only string
            ("", "", ""),        # empty string
        ],
    )
    def test_init_and_strip(self, input_str, expected_raw, expected_data):
        """Ensure raw_data stores original string and data is stripped."""
        line_data = LineData(input_str)
        assert line_data.raw_data == expected_raw
        assert line_data.data == expected_data

    def test_call_creates_new_instance(self):
        """Calling an instance should return a new LineData object."""
        line_data = LineData("hello")
        new_ld = line_data("   world   ")
        assert isinstance(new_ld, LineData)
        assert new_ld.raw_data == "   world   "
        assert new_ld.data == "world"

    @pytest.mark.parametrize(
        "input_str, expected_leading, expected_is_leading",
        [
            ("   hello   ", "   ", True),
            ("hello   ", "", False),
            ("   hello", "   ", True),
            ("hello", "", False),
        ],
    )
    def test_leading_properties(self, input_str, expected_leading, expected_is_leading):
        """Verify leading whitespace extraction and boolean flags."""
        line_data = LineData(input_str)
        assert line_data.leading == expected_leading
        assert line_data.is_leading == expected_is_leading

    @pytest.mark.parametrize(
        "input_str, expected_trailing, expected_is_trailing",
        [
            ("   hello   ", "   ", True),
            ("hello   ", "   ", True),
            ("   hello", "", False),
            ("hello", "", False),
        ],
    )
    def test_trailing_properties(self, input_str, expected_trailing, expected_is_trailing):
        """Verify trailing whitespace extraction and boolean flags."""
        line_data = LineData(input_str)
        assert line_data.trailing == expected_trailing
        assert line_data.is_trailing == expected_is_trailing