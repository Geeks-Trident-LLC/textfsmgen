"""
textfsmgen.tools.translator
==========================

Utilities for building and applying translator nodes used in snippet parsing.
"""


from textfsmgen.tools.token import (
    WhitespaceSnippet,
    TokenSnippet,
    LineSnippet
)


class SnippetTranslator:
    def __init__(
        self, raw, variable_flag=True, notation_flag=False,
        group_flag=False, generic_flag=False, split_arg="/",
        explain_flag=False,
    ):
        self._raw = raw

        self.variable_flag = variable_flag
        self.notation_flag = notation_flag
        self.group_flag = group_flag
        self.generic_flag = generic_flag
        self.split_arg = split_arg
        self.explain_flag = explain_flag

        self._parsed = False
        self._translator = None
        self.parse()

    def __bool__(self): return self._parsed

    def __len__(self): return 1 if self._parsed else 0

    @property
    def raw(self): return self._raw

    @property
    def parsed(self): return self._parsed

    @property
    def snippet(self): return self._translator.snippet if self else ""

    @property
    def pattern(self): return  self._translator.pattern if self else ""

    @property
    def pattern_statement(self): return self._translator.pattern_statement if self else ""

    def parse(self):
        """Run available parsers and stop at the first successful match."""
        if not self._raw:
            return

        parsers = [self._parse_whitespace, self._parse_group, self._parse_line,]
        for parser in parsers:
            if parser():
                return

    def _parse_whitespace(self):
        """Parse raw text as a whitespace snippet."""

        var_name = "v0" if self.variable_flag else ""
        node = WhitespaceSnippet(self._raw, var_name=var_name)
        self._parsed = bool(node)
        if node:
            self._translator = node

        return self._parsed

    def _parse_group(self):
        """Parse raw text as a group snippet."""
        if not self.group_flag:
            return False

        var_name = "v0" if self.variable_flag else ""
        lines = self._raw.splitlines()
        node = TokenSnippet(*lines, var_name=var_name, generic=self.generic_flag)
        self._parsed = bool(node)
        if node:
            self._translator = node

        return self._parsed

    def _parse_line(self):
        """Parse the first non-empty line into a LineSnippet."""
        if self.group_flag:
            return False

        lines = [line for line in self._raw.splitlines() if line.strip()]
        if not lines:
            return False

        node = LineSnippet(
            lines[0],
            with_var=self.variable_flag,
            with_notation=self.notation_flag,
            split_divider=self.split_arg,
            generic=self.generic_flag,
        )

        self._parsed = bool(node)
        if node:
            self._translator = node

        return self._parsed


class IterateTranslator:
    def __init__(self, original):
        self.original = original
