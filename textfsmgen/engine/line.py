"""
textfsmgen.engine.line
======================

Utilities for representing and inspecting a single line of text.
"""

from textfsmgen.libs import text


class LineData:
    """
    Line wrapper for string input with utilities to
    inspect leading and trailing whitespace.
    """
    def __init__(self, data):
        self.raw_data = str(data)
        self.data = self.raw_data.strip()

    def __call__(self, *args, **kwargs):
        return self.__class__(*args, **kwargs)

    @property
    def leading(self):
        return text.Line.get_leading(self.raw_data)

    @property
    def trailing(self):
        # Whitespace-only lines are treated as leading, not trailing
        if self.raw_data.strip():
            return text.Line.get_trailing(self.raw_data)
        return ""

    @property
    def is_leading(self):
        return self.leading != ""

    @property
    def is_trailing(self):
        return self.trailing != ""
