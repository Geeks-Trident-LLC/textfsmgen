"""
textfsmgen.engine.__init__
==========================

Initialization for the TextFSM parsing engine.
"""     # noqa

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
        if self.raw_data.strip():
            return text.Line.get_trailing(self.raw_data)
        return ""

    @property
    def is_leading(self):
        return self.leading != ""

    @property
    def is_trailing(self):
        return self.trailing != ""
