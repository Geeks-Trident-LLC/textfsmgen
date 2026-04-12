import re

from textfsmgen.libs.text import Line
from textfsmgen.libs.text import get_list_of_lines

class SnippetBase:
    """Base class for snippet parsers."""

    def __init__(self, *items, var_name="", exact=False):
        self._raw = items
        self._items = get_list_of_lines(*items)
        self._var_name = var_name
        self._exact = exact

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
    def has_data(self): return any(bool(i) for i in self._data_list)

    @property
    def leading_list(self): return self._leading_list

    @property
    def is_leading(self): return any(bool(i) for i in self._leading_list)

    @property
    def trailing_list(self): return self._trailing_list

    @property
    def is_trailing(self): return any(bool(i) for i in self._trailing_list)

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

        return f"wss({', '.join(params)})"

    def parse(self):
        """Evaluate items and update parsed/empty flags."""

        if not self._items:
            return

        parts = []
        for item in self._items:
            if item == "":
                self._allow_empty = True
                continue
            parts.append(bool(re.fullmatch(r"\s+", item)))

        self._parsed = all(parts)


class TokenSnippet(SnippetBase):
    pass
