"""
textfsmgen.tools.snippet
========================

Helpers for building and manipulating snippet objects used during parsing.
"""

import re

from textfsmgen.libs.pattern import PATTERN
from textfsmgen.libs.utils import split_by_matches
from textfsmgen.libs.text import (
    Line,
    is_punctuation,
    get_list_of_lines,
)

from textfsmgen.engine.translate import make_translator
from textfsmgen.tools.explain import SnippetExplanation

from textfsmgen.core.patterns import LinePattern, ElementPattern

from textfsmgen.libs.text import enclose_string


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

        self._bare_snippet = ""
        self._explanation = ""

        self.normalize()
        self.parse()

    def __bool__(self):
        return self._parsed

    @property
    def explanation(self):
        return self._explanation

    @property
    def raw(self):
        """Return original items."""
        return self._raw

    @property
    def data_list(self):
        return self._data_list

    @property
    def has_data(self):
        return any(self._data_list)

    @property
    def leading_list(self):
        return self._leading_list

    @property
    def is_leading(self):
        return any(self._leading_list)

    @property
    def is_ws_leading(self):
        return any(bool(re.search(r"[^ \r\n]", i)) for i in self._leading_list)

    @property
    def trailing_list(self):
        return self._trailing_list

    @property
    def is_trailing(self):
        return any(self._trailing_list)

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
    def keyword(self):
        return self._keyword

    @property
    def bare_snippet(self):
        return self._bare_snippet

    @property
    def snippet(self):
        """Return the formatted snippet, or empty string if not parsed."""
        return self.build() if self._parsed else ""

    @property
    def pattern(self):
        """Return the formatted pattern, or empty string if not parsed."""
        snippet = self.snippet
        return ElementPattern(snippet) if snippet else ""

    @property
    def pattern_statement(self):
        return create_pattern_statement(self.snippet, self.pattern)

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

    def explain(self, snippet: str, samples=None) -> str:
        """Generate an explanation for the snippet using provided or stored samples."""
        if not self:
            return ""

        items = [item.strip() for item in self._items]
        data = samples or (items if any(items) else self._items)

        node = SnippetExplanation(snippet, test_samples=data)
        explanation = node.explanation

        if samples is None:
            self._explanation = explanation

        return explanation

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
        self._bare_snippet = f"{self._keyword}({params})"
        self._explanation = self.explain(self._bare_snippet)
        return self._bare_snippet

    def parse(self):
        """Evaluate items and update parsed/empty flags."""

        if not any(self._items):
            return

        self._allow_empty = any(item == "" for item in self._items)

        self._parsed = all(re.fullmatch(r"\s+", item) for item in self._items if item)


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
        self._bare_snippet = f"{self._keyword}({params})"

        explanation = self.explain(self._bare_snippet)

        sep = "=" * 72
        # leading_explanation, trailing_explanation = "", ""
        if re.fullmatch(r"\w+[(][)]", self.leading_snippet):
            leading_explanation = self.explain(self.leading_snippet, self.leading_list)
            if (
                "Operation: " in leading_explanation
                and leading_explanation not in explanation
            ):
                explanation = f"{leading_explanation}\n\n{sep}\n\n{explanation}"

        if re.fullmatch(r"\w+[(][)]", self.trailing_snippet):
            trailing_explanation = self.explain(
                self.trailing_snippet, self.trailing_list
            )
            if (
                "Operation: " in trailing_explanation
                and trailing_explanation not in explanation
            ):
                explanation = f"{explanation}\n\n{sep}\n\n{trailing_explanation}"

        self._explanation = explanation

        return f"{self.leading_snippet}{self._bare_snippet}{self.trailing_snippet}"

    def parse(self):
        """Evaluate items and update parsed/empty flags."""

        if not any(self._data_list):
            return

        self._parser = make_translator(*self._data_list, multiple=True)
        self._parsed = bool(self._parser)


class LineSnippet:
    def __init__(
        self, line, generic=False, split_divider="/", with_var=True, with_notation=False
    ):
        self._raw = line
        self._with_var = with_var
        self._split_divider = split_divider.strip()
        self._with_notation = with_notation
        self._generic = generic

        self._tokens = []

        self._parsed = False
        self._explanation = ""

        self.parse_tokens()

    def __bool__(self):
        return self._parsed

    @property
    def raw(self):
        return self._raw

    @property
    def data(self):
        return self._raw.strip()

    @property
    def explanation(self):
        return self._explanation

    @property
    def snippet(self):
        """Return the rendered snippet by joining token strings."""
        if not self._parsed:
            return ""

        mapping = {}
        parts = []
        for tok in self._tokens:
            if isinstance(tok, str):
                parts.append(tok)
                continue
            parts.append(tok.snippet)
            mapping[tok.bare_snippet] = tok.explanation

        sep = "=" * 72
        self._explanation = f"\n\n{sep}\n\n".join(mapping.values())
        return "".join(parts)

    @property
    def pattern(self):
        snippet = self.snippet
        return LinePattern(snippet) if snippet else ""

    @property
    def pattern_statement(self):
        return create_pattern_statement(self.snippet, self.pattern)

    def _split_leading_notation(self, data):
        """Split text into (leading notation, core text) based on punctuation rules."""
        if not self._with_notation or is_punctuation(data):
            return "", data

        if re.match(r"(?i)((::[a-z0-9])|([.][0-9]))", data):
            return "", data

        match = re.match(rf"(?P<puncts>{PATTERN.PUNCTS})", data)

        if not match:
            return "", data

        puncts = match.group("puncts")
        unique = set(puncts)
        if len(unique) == 1:
            return puncts, data[len(puncts) :]
        return puncts[0], data[1:]

    def _split_trailing_notation(self, data):
        """Split text into (core, trailing notation) based on punctuation rules."""

        if not self._with_notation or is_punctuation(data):
            return data, ""

        # Skip cases like "a::" or "3."
        if re.search(r"(?i)(([a-z0-9]::)|([0-9][.]))$", data):
            return data, ""

        match = re.search(rf"(?P<puncts>{PATTERN.PUNCTS})$", data)

        if not match:
            return data, ""

        puncts = match.group("puncts")
        unique = set(puncts)
        if len(unique) == 1:
            return data[: -len(puncts)], puncts

        # Mixed punctuation: keep only the last char as notation
        return data[:-1], puncts[-1]

    def _split_by_divider(self, data):
        """Split text using the configured divider, preserving non-empty parts."""
        if not self._split_divider:
            return [data]

        pattern = rf"[{re.escape(self._split_divider)}]+"
        parts = split_by_matches(data, pattern)
        if parts and parts[-1] == "":
            parts.pop()

        return parts

    def parse_tokens(self):
        """Parse raw text into token snippets, punctuation, and notation parts."""
        tokens = []
        index = 0

        for chunk in split_by_matches(self._raw):
            if not chunk:
                continue

            # Whitespace or pure punctuation → passthrough
            if chunk.isspace() or is_punctuation(chunk):
                tokens.append(chunk)
                continue

            # Leading notation
            lead, remainder = self._split_leading_notation(chunk)
            if lead:
                tokens.append(lead)

            # Divider-based splitting
            *segments, remainder = self._split_by_divider(chunk)
            for segment in segments:
                if is_punctuation(segment):
                    tokens.append(segment)
                    continue

                var_name = f"v{index}" if self._with_var else ""
                index += 1

                snippet = TokenSnippet(
                    segment, var_name=var_name, generic=self._generic
                )
                self._parsed = bool(snippet)
                tokens.append(snippet)

            # Trailing notation
            core, trail = self._split_trailing_notation(remainder)

            var_name = f"v{index}" if self._with_var else ""
            index += 1

            core_token = TokenSnippet(core, var_name=var_name, generic=self._generic)
            self._parsed = bool(core_token)
            tokens.append(core_token)

            if trail:
                if is_punctuation(trail):
                    tokens.append(trail)
                else:
                    var_name = f"v{index}" if self._with_var else ""
                    index += 1

                    trail_token = TokenSnippet(
                        trail, var_name=var_name, generic=self._generic
                    )
                    self._parsed = bool(trail_token)
                    tokens.append(trail_token)

        self._tokens = tokens[:]


def create_pattern_statement(snippet: str, pattern: str) -> str:
    """Return a formatted pattern statement with a snippet comment block."""
    if not pattern:
        return ""

    snippet_comment = f"#  {snippet!r}"
    width = min(max(len(snippet_comment), 40), 60)
    border = "#" * width

    lines = [
        border,
        "# Equivalent snippet conversion:",
        snippet_comment,
        border,
        f"pattern = r{enclose_string(pattern)}",
    ]
    return "\n".join(lines)
