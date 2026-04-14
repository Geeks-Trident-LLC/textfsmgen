"""
textfsmgen.tools.translator
==========================

Utilities for building and applying translator nodes used in snippet parsing.
"""
import re
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

from textfsmgen.libs.text import (
    get_list_of_lines,
    enclose_string
)

from textfsmgen.core.patterns import LinePattern

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


class ScriptBuilder:
    def __init__(self, raw, snippet, group_flag=False):
        self._snippet = snippet
        self._raw = raw
        self._group_flag = group_flag

        self._lines = get_list_of_lines(raw)
        self._data_lines = [line for line in get_list_of_lines(raw) if line.strip()]

        self._test_data_list = []

        self._script = "abc"
        self._result = "xyz"

    @property
    def raw(self): return self._raw

    @property
    def snippet(self): return self._snippet

    @property
    def script(self):
        comment = self.build_comment()
        python_code = self.build_python_code()
        self.build_execution_result()
        return f"{comment}\n\n{python_code}"

    @property
    def result(self): return self._result

    def is_whitespaces_test_data(self):
        if not any(self._lines):
            return False
        return not any(self._data_lines)

    def build_comment(self):
        width = 72
        border = "#" * width
        lines = [border]
        footer = ""

        # --- Raw Data -----------------------------------------------------------
        raw_repr = repr(self._raw)
        if len(raw_repr) <= width + 10 or len(self._lines) == 1:
            lines.append(f"# Raw Data          : {raw_repr}")
        else:
            lines.append("# Raw Data          :")
            for line in self._lines:
                lines.append(f"#  - {line!r}")

        # --- Test Data ----------------------------------------------------------
        if self.is_whitespaces_test_data():
            lines.append(f"# Test Data         : {self._lines!r}")
            self._test_data_list = self._lines[:]

        else:
            if self._group_flag:
                self._test_data_list = self._lines[:]

                group_repr = repr(self._lines)
                if len(group_repr) <= width or len(self._lines) == 1:
                    lines.append(f"# Group of Test Data: {group_repr}")
                else:
                    lines.append("# Group of Test Data:")
                    for line in self._lines:
                        lines.append(f"#  - {line!r}")

            else:
                first_line = self._data_lines[0]
                lines.append(f"# Test Data         : {first_line!r}")
                self._test_data_list = self._data_lines[:1]

                if len(self._data_lines) > 1:
                    footer = (
                        "# Note: For simplicity, this app handles only "
                        "one line at a time."
                    )

        # --- Snippet & Pattern --------------------------------------------------
        lines.append(f"# Snippet           : {self._snippet!r}")

        pattern = LinePattern(self._snippet)
        lines.append(f"# Generated Pattern : {pattern!r}")

        # --- Footer -------------------------------------------------------------
        if footer:
            lines.append("# " + "=" * (width - 2))
            lines.append(footer)

        lines.append(border)
        return "\n".join(lines)

    def build_python_code(self):
        group_flag = True if self.is_whitespaces_test_data() else self._group_flag
        pattern = LinePattern(self._snippet)
        lst = [
            "import re",
            "from textfsmgen.core.patterns import LinePattern",
            "from textfsmgen.libs.text import get_list_of_lines",
            "",
            "",
            "# When raw data consists entirely of whitespace, group_flag is always True",
            f"group_flag = {group_flag}",
            "",
            f"raw_data = {enclose_string(self._raw)}",
            "",
            f"# When group_flag is False, only the first non-empty line is used",
            f"if not group_flag:",
            f"    lines = [line for line in get_list_of_lines(raw_data) if line.strip()]",
            f'    assert lines, "No non-empty lines found in raw_data"',
            f"    test_data_list = lines[0:1]",
            f"else:",
            f"    test_data_list = get_list_of_lines(raw_data)",
            "",
            f"pattern = r{enclose_string(pattern)}",
            "",
            f"# Run pattern against each test data line",
            "",
            f"for test_data in test_data_list:",
            f"    match = re.fullmatch(pattern, test_data)",
            '    assert match is not None, f"Pattern failed on: {repr(test_data)}"',
            f"    print(match.groupdict() or match)",
            "",

        ]

        return "\n".join(lst)

    def build_execution_result(self):
        """
        Execute the generated pattern against test data and capture stdout, stderr,
        and any exception traceback into self._result.
        """
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        trace_text = None

        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            try:
                pattern = LinePattern(self._snippet)

                for text in self._test_data_list:
                    match = re.fullmatch(pattern, text)
                    assert match is not None
                    print(match.groupdict() or match)

            except Exception:   # noqa
                trace_text = traceback.format_exc()

        # Combine captured output
        result = out_buf.getvalue()

        err_text = err_buf.getvalue()
        if err_text:
            result = f"{result}\n{err_text}"

        if trace_text:
            result = f"{result}\n{trace_text}"

        self._result = result
