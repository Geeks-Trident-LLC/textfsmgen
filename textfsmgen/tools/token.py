import re

from textfsmgen.libs.text import Line
from textfsmgen.libs.text import get_list_of_lines
from textfsmgen.engine.translate import make_translator

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
        self._keyword = ""
        self._parser = None

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
        return base if all(self._leading_list) else f"optional_{base}"

    @property
    def trailing_snippet(self):
        """Return trailing snippet representation."""
        if not self.is_trailing:
            return ""

        base = "wss()" if self.is_ws_trailing else "spaces()"
        return base if all(self._trailing_list) else f"optional_{base}"

    @property
    def keyword(self): return self._keyword

    @property
    def snippet(self):
        """Return the formatted snippet, or empty string if not parsed."""
        return self.build() if self._parsed else ""

    def normalize(self):
        for item in self._items:
            line = Line(item)
            self._leading_list.append(line.leading)
            self._trailing_list.append(line.trailing)
            if line.data:
                self._data_list.append(line.data)
            else:
                self._allow_empty = True

    def keyword_params(self):
        """Return formatted keyword parameters."""
        parts = []
        if self._var_name:
            parts.append(f"var_{self._var_name}")
        if self._allow_empty:
            parts.append("or_empty")
        return ", ".join(parts)

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
        if not self:
            return ""
        params = self.keyword_params()
        self._keyword = "wss" if self.is_ws_leading else "spaces"
        return f"{self._keyword}({params})"

    def parse(self):
        """Evaluate items and update parsed/empty flags."""

        if not self._items:
            return

        self._allow_empty = any(item == "" for item in self._items)

        self._parsed = all(
            re.fullmatch(r"\s+", item) for item in self._items if item
        )


class TokenSnippet(SnippetBase):
    def build(self):
        """Return the snippet string."""
        if not self:
            return ""

        params = self.keyword_params()
        snippet = self._parser.to_snippet(generic=self._generic)
        if "(" not in snippet:
            return ""

        self._keyword, _ = snippet.split("(", maxsplit=1)
        return f"{self.leading_snippet}{self._keyword}({params}){self.trailing_snippet}"

    def parse(self):
        """Evaluate items and update parsed/empty flags."""

        if not self._data_list:
            return

        self._parser = make_translator(*self._data_list, multiple=True)
        self._parsed = bool(self._parser)

