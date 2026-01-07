"""
Unit tests for the `textfsmgen.gpcommon.GPCommon` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpcommon/test_gpcommon_module.py
    or
    $ python -m pytest tests/unit/gpcommon/test_gpcommon_module.py
"""
import pytest
from textfsmgen.gpcommon import get_line_position_by
from textfsmgen.gpcommon import get_fixed_line_snippet


class TestGetLinePositionBy:
    """
    Unit tests for the `get_line_position_by` function in `textfsmgen.gpcommon`.
    """

    def setup_method(self):
        """Setup test fixture with sample lines."""
        self.lines = [
            "line1: _abc =123",
            "line2: ____ ===",
            "(line11]: ?.?",
            "line22: 1.23",
        ]

    @pytest.mark.parametrize(
        "item, expected",
        [
            # None input should return None
            (None, None),

            # Integer index should return the same index if valid
            (1, 1),

            # Wildcard patterns
            ("--wildcard line[[:digit:]]", 0),
            ("--wildcard line[[:digit:]][[:digit:]]", 2),
            ("--wildcard _* =*", 0),
            ("--wildcard _{2,} ={2,}", 1),

            # Regex patterns
            (r"--regex line[0-9]{2,}", 2),
            (r"--regex _\w+ =\w+", 0),
            (r"--regex _{2,} ={2,}", 1),
            (r"--regex [?]+[.][?]", 2),
            (r"--regex [0-9]+[.][0-9]+", 3),
        ],
    )
    def test_get_line_position_by(self, item, expected):
        """
        Verify that `get_line_position_by` returns the correct line index
        for various input types.
        """
        result = get_line_position_by(self.lines, item)
        assert result == expected, (
            f"For item={item!r}, expected {expected!r} but got {result!r}"
        )


class TestGetFixedLineSnippet:
    """
    Unit tests for the `get_fixed_line_snipp` function in `textfsmgen.gpcommon`.
    """

    def setup_method(self):
        """Setup test fixture with sample lines."""
        self.lines = [
            " ",
            " \t ",
            "line1: _abc 1 23",
            "line2: 1.1.1.1 a::b",
            "line3: ........ abc",
            "line22: 1.23",
        ]

    @pytest.mark.parametrize(
        "index, expected",
        [
            (0, "start() end(space)"),
            (1, "start() end(whitespace)"),
            (2, "line1: _abc digit() digits()"),
            (3, "line2: 1.1.1.1 a::b"),
            (-1, "line22: number()"),
        ],
    )
    def test_get_fixed_line_snippet_passing_index(self, index, expected):
        """
        Verify that `get_fixed_line_snippet` returns the correct line index
        for various input types.
        """
        result = get_fixed_line_snippet(self.lines, index=index)
        assert result == expected, (
            f"For index={index!r}, expected {expected!r} but got {result!r}"
        )

    @pytest.mark.parametrize(
        "line, expected",
        [
            ("", "start() end(space)"),
            (" \t ", "start() end(whitespace)"),

            ("line1: _abc 1 23", "line1: _abc digit() digits()"),
            ("line2: 1.1.1.1 a::b", "line2: 1.1.1.1 a::b"),
            ("line3: ++++++++ abc", "line3: puncts() abc"),
            ("line22: 1.23", "line22: number()"),
        ],
    )
    def test_get_fixed_line_snippet_passing_line(self, line, expected):
        """
        Verify that `get_fixed_line_snippet` returns the correct line index
        for various input types.
        """
        result = get_fixed_line_snippet(self.lines, line=line)
        assert result == expected