import re

from textfsmgen.libs.text import Line
from textfsmgen.libs.text import get_list_of_lines

class SnippetBase:
    """Base class for snippet parsers."""

    def __init__(self, *items, var_name="", generic=False):
        self._raw = items
        self._items = get_list_of_lines(*items)
        self._var_name = var_name
        self._generic = generic

        self._data_list = []
        self._leading_list = []
        self._trailing_list = []

        self._parsed = False
        self._allow_empty = False

        self.normalize()
        self.parse()

    def __bool__(self): return self._parsed

    def __len__(self): return 1 if self._parsed else 0

    @property
    def raw(self):
        """Return original items."""
        return self._raw

    @property
    def data_list(self): return self._data_list

    @property
    def has_data(self): return any(self._data_list)

    @property
    def leading_list(self): return self._leading_list

    @property
    def is_leading(self): return any(self._leading_list)

    @property
    def is_ws_leading(self):
        return any(bool(re.search(r"[^ \r\n]", i)) for i in self._leading_list)

    @property
    def trailing_list(self): return self._trailing_list

    @property
    def is_trailing(self): return any(self._trailing_list)

    @property
    def is_ws_trailing(self):
        return any(bool(re.search(r"[^ \r\n]", i)) for i in self._trailing_list)

    @property
    def leading_snippet(self):
        """Return leading snippet representation."""
        if not self.is_leading:
            return ""

        base = "wss()" if self.is_ws_leading else "spaces()"
        return f"optional_{base}" if any(item == "" for item in self._leading_list) else base

    @property
    def trailing_snippet(self):
        """Return trailing snippet representation."""
        if not self.is_leading:
            return ""

        base = "wss()" if self.is_ws_trailing else "spaces()"
        return f"optional_{base}" if any(item == "" for item in self._trailing_list) else base


    @property
    def snippet(self):
        """Return the formatted snippet, or empty string if not parsed."""
        return self.build() if self._parsed else ""

    def normalize(self):
        for item in self._items:
            line = Line(item)
            self._leading_list.append(line.leading)
            self._trailing_list.append(line.trailing)
            self._data_list.append(line.data)
            if not line.data:
                self._allow_empty = True

    # --- Methods subclasses must implement ---------------------------------

    def build(self):
        """Return the snippet string."""
        raise NotImplementedError("Subclasses must implement build()")

    def parse(self):
        """Parse items and update internal state."""
        raise NotImplementedError("Subclasses must implement parse()")


class WhitespaceSnippet(SnippetBase):
    """Parse whitespace items and build a wss(...) snippet."""

    def build(self):
        """Return the snippet string."""
        params = []
        if self._var_name:
            params.append(f"var_{self._var_name}")
        if self._allow_empty:
            params.append("or_empty")
        keyword = "wss" if self.is_ws_leading else "spaces"
        return f"{keyword}({', '.join(params)})"

    def parse(self):
        """Evaluate items and update parsed/empty flags."""

        if not self._items:
            return

        self._allow_empty = any(item == "" for item in self._items)

        self._parsed = all(
            re.fullmatch(r"\s+", item) for item in self._items if item
        )


class TokenSnippet(SnippetBase):
    pass
