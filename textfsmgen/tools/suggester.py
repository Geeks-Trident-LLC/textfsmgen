"""
textfsmgen.tools.translator
==========================

Utilities for building and applying translator nodes used in snippet parsing.
"""
import re
import io

import random

import traceback
from contextlib import redirect_stdout, redirect_stderr

from textfsmgen.libs.text import (
    get_list_of_lines,
    enclose_string
)

from textfsmgen.core.patterns import LinePattern
from textfsmgen.libs.utils import split_by_matches
from textfsmgen.libs.token import tokenize, CallNode

from textfsmgen.tools.token import (
    WhitespaceSnippet,
    TokenSnippet,
    LineSnippet
)


class SnippetSuggester:
    def __init__(
        self, raw, variable_flag=True, notation_flag=False,
        group_flag=False, generic_flag=False, split_arg="/",
    ):
        self._raw = raw

        self.variable_flag = variable_flag
        self.notation_flag = notation_flag
        self.group_flag = group_flag
        self.generic_flag = generic_flag
        self.split_arg = split_arg

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

    @property
    def explanation(self): return self._translator.explanation if self else ""

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


class IterateSuggester:
    def __init__(self, raw, snippet, group_flag=False):
        self._raw = raw
        self._original_snippet = snippet
        self._group_flag = group_flag

        self._snippet = ""
        self._script = ""
        self._result = ""

        self._error = ""
        self._warning = ""

        self._is_wss_or_group = False

        self._test_data_list = []

        self._pad_numbers = [f"{i:03}" for i in range(100)]

        self.build_test_data()

        self.validate_snippet_match(self._original_snippet)

        self.translate_snippet()


    def __bool__(self):
        return bool(self._snippet) or not any([self._error, self._warning])

    def __len__(self): return 1 if self else 0

    @property
    def raw(self): return self._raw

    @property
    def original_snippet(self): return self._original_snippet

    @property
    def warning(self): return self._warning

    @property
    def error(self): return self._error

    @property
    def snippet(self): return self._snippet

    @property
    def script(self): return self._script

    @property
    def result(self): return self._result

    def build_test_data(self):
        """
        Normalize raw input into a list of test data lines based on whitespace
        handling and the group_flag setting.
        """
        lines = get_list_of_lines(self._raw)
        non_empty = [line for line in lines if line.strip()]

        # No lines at all
        if not any(lines):
            self._warning = "No test data was found."
            return

        # Use all lines when:
        # - all lines are whitespace, or
        # - group_flag is enabled
        if not any(non_empty) or self._group_flag:
            self._test_data_list = lines.copy()
            self._is_wss_or_group = True
            return

        # Otherwise use only the first non-empty line
        self._test_data_list = non_empty[:1]

    def should_keep_in_snippet(self):
        """Return True if any token contains a 'keep' parameter."""
        return any(
            p.has_parameter("keep")
            for p in tokenize(self._original_snippet) if not p.is_plain
        )

    def token_has_non_default_var(self, token): # noqa
        """Return True if the token has var_* parameters excluding var_v<number>."""
        if not isinstance(token, CallNode):
            return False

        var_any = token.has_matching_parameter(r"(?i)var_\w+")
        var_default = token.has_matching_parameter(r"(?i)var_v\d+")

        return var_any and not var_default

    def token_has_default_var(self, token): # noqa
        """Return True if the token has a default var_v<number> parameter."""
        if not isinstance(token, CallNode):
            return False

        var_any = token.has_matching_parameter(r"(?i)var_\w+")
        var_default = token.has_matching_parameter(r"(?i)var_v\d+")

        return var_any and var_default

    def has_default_var(self):
        """Return True if any token in the snippet contains a default var_v<number>."""
        return any(
            self.token_has_default_var(token)
            for token in tokenize(self._original_snippet)
        )

    def has_non_default_var(self):
        """Return True if any token in the snippet contains a non-default var_*."""
        return any(
            self.token_has_non_default_var(token)
            for token in tokenize(self._original_snippet)
        )

    def validate_snippet_match(self, snippet):
        """
        Validate that the original snippet matches all test data lines.
        Sets _warning or _error when the snippet or pattern is incompatible.
        """
        if not self:
            return

        try:
            pattern = LinePattern(snippet)

            for text in self._test_data_list:
                if re.fullmatch(pattern, text) is None:
                    self._warning = (
                        "Incompatible Snippet: Data does not match the pattern\n"
                        f"  + Given Snippet    : {self._original_snippet!r}\n"
                        f"  + Translate Pattern: {pattern!r}\n"
                        f"  + Data             : {text!r}"
                    )
                    return

        except Exception:   # noqa
            self._error = traceback.format_exc()
            return

    def translate_wss_or_group(self):
        """
        Remove the 'keep' parameter from snippet functions while preserving
        all other parameters and original ordering.
        """
        pattern = r"\w+\([^)]*\)"
        parts = []

        for token in split_by_matches(self._original_snippet, pattern):
            # Non-function tokens pass through unchanged
            if not re.fullmatch(pattern, token):
                parts.append(token)
                continue

            name, raw_params = token[:-1].split("(", 1)
            params = re.split(r"\s*,\s*", raw_params)

            # Drop any 'keep' parameter (case-insensitive)
            filtered = [p for p in params if p.lower() != "keep"]

            if filtered:
                parts.append(f"{name}({', '.join(filtered)})")
            else:
                # No parameters left → keep empty parentheses
                parts.append(f"{name}()")

        self._snippet = "".join(parts)

    def translate_snippet(self):
        if not self:
            return

        # Special-case: whitespace/group-style snippet
        if self._is_wss_or_group:
            self.translate_wss_or_group()
            builder = ScriptBuilder(self._raw, self._snippet, group_flag=self._group_flag)
            self._script = builder.script
            self._result = builder.result
            return

        if not self.should_keep_in_snippet() and not self.has_non_default_var():
            builder = ScriptBuilder(self._raw, self._original_snippet, group_flag=self._group_flag)
            self._snippet = self._original_snippet
            self._script = builder.script
            self._result = builder.result
            return

        tokens = tokenize(self._original_snippet)
        rewritten = []

        for token in tokens:
            # Non-token pass through unchanged
            if token.is_plain:
                rewritten.append(token)
                continue

            if self.token_has_non_default_var(token):
                rewritten.append(token)
                continue

            random.shuffle(self._pad_numbers)
            var_name = "var_data_" + "".join(self._pad_numbers[:4])

            # No parameters → inject data variable
            if token.has_no_parameters:
                result = token if self.has_default_var() else token.with_parameters(var_name)
                rewritten.append(result)
                continue

            # Drop 'keep' parameter
            if token.has_parameter("keep"):
                token.remove_parameter("keep")
                param = token.remove_matching_parameter(r"var_v\d+")
                new_param = re.sub(r"(?i)var_v", "var_cv", param)
                token.prepend_parameter(new_param)
                rewritten.append(token.new)
                continue

            # Remove existing var_* parameters
            token.remove_matching_parameter(r"(?i)var_\w+")

            # Prepend new data variable
            token.prepend_parameter(var_name)
            rewritten.append(token.new)

        new_snippet = "".join(rewritten)
        # Validate translated snippet against test data
        pattern = LinePattern(new_snippet)
        match = re.fullmatch(pattern, self._test_data_list[0])

        if not match:
            self._warning = (
                "Snippet analysis failed: translated pattern did not match test data.\n"
                "  + This indicates an unexpected translation outcome.\n"
                "  + Please report this as Bug Case #1."
            )
            return

        if not match.groupdict():
            self._warning = (
                "Snippet analysis failed: pattern matched but produced no variables.\n"
                "  + The snippet translation yielded zero captured groups.\n"
                "  + Please report this as Bug Case #2."
            )
            return

        # Replace temporary var_data_* placeholders with matched values
        for key, value in match.groupdict().items():
            if re.fullmatch(r"(?i)data_[0-9]{12}", key):
                for i, part in enumerate(rewritten):
                    if key in part:
                        rewritten[i] = value

        snippet = "".join(rewritten)
        builder = ScriptBuilder(self._raw, snippet, group_flag=self._group_flag)

        self._snippet = snippet
        self._script = builder.script
        self._result = builder.result


class ScriptBuilder:
    def __init__(self, raw, snippet, group_flag=False):
        self._snippet = snippet
        self._raw = raw
        self._group_flag = group_flag

        self._lines = get_list_of_lines(raw)
        self._data_lines = [line for line in get_list_of_lines(raw) if line.strip()]

        self._test_data_list = []

        self._script = ""
        self._result = ""

    @property
    def raw(self): return self._raw

    @property
    def snippet(self): return self._snippet

    @property
    def script(self):
        comment = self.build_comment()
        python_code = self.build_python_code()
        self.build_execution_result()
        self._script = f"{comment}\n\n{python_code}"
        return self._script

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
            lines.append(f"# Raw Data: {raw_repr}")
        else:
            lines.append("# Raw Data:")
            for line in self._lines:
                lines.append(f"#  - {line!r}")

        # --- Test Data ----------------------------------------------------------
        if self.is_whitespaces_test_data():
            lines.append(f"# Sample  : {self._lines!r}")
            self._test_data_list = self._lines[:]

        else:
            if self._group_flag:
                self._test_data_list = self._lines[:]

                group_repr = repr(self._lines)
                if len(group_repr) <= width or len(self._lines) == 1:
                    lines.append(f"# Samples : {group_repr}")
                else:
                    lines.append("# Samples :")
                    for line in self._lines:
                        lines.append(f"#  - {line!r}")

            else:
                first_line = self._data_lines[0]
                lines.append(f"# Sample  : {first_line!r}")
                self._test_data_list = self._data_lines[:1]

                if len(self._data_lines) > 1:
                    footer = (
                        "# Note: For simplicity, this app handles only "
                        "one line at a time."
                    )

        # --- Snippet & Pattern --------------------------------------------------
        lines.append(f"# Snippet : {self._snippet!r}")

        pattern = LinePattern(self._snippet)
        lines.append(f"# Pattern : r{enclose_string(pattern)}")

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
            "# When group_flag is False, only the first non-empty line is used",
            "if not group_flag:",
            "    lines = [line for line in get_list_of_lines(raw_data) if line.strip()]",
            '    assert lines, "No non-empty lines found in raw_data"',
            "    samples = lines[0:1]",
            "else:",
            "    samples = get_list_of_lines(raw_data)",
            "",
            f"pattern = r{enclose_string(pattern)}",
            "",
            "# Run pattern against each test data line",
            "",
            "for sample in samples:",
            "    match = re.fullmatch(pattern, sample)",
            '    assert match is not None, f"Pattern failed on: {repr(sample)}"',
            "    print(match.groupdict() or match)",
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
