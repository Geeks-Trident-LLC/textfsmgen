"""
textfsmgen.engine.category
==========================

Provides category definitions and grouping utilities for grammar patterns
used in the TextFSM Generator framework. This module centralizes the
classification of grammar pattern categories, ensuring consistent handling
across parsing, translation, and validation workflows.
"""

import re
from typing import Optional

from textfsmgen.core.patterns import TextPattern
from textfsmgen.libs import PATTERN
from textfsmgen.libs import text
from textfsmgen.libs import utils

from textfsmgen.engine.translate import PatternTranslator
from textfsmgen.engine import LineData
from textfsmgen.exceptions import RuntimeException

from textfsmgen.engine.common import get_line_position_by
from textfsmgen.engine.common import get_fixed_line_snippet


PATTERN_CRNL = r'\r?\n|\r'


class VarRegistry:
    """Generate stable, unique variable names based on extracted text."""

    def __init__(self):
        self._registry = dict()

    def assign(self, var_txt, value):
        """
        Return a unique variable name derived from `var_txt`.
        If the same label maps to the same value, reuse the name.
        Otherwise, append a numeric suffix.
        """

        var_name = re.sub(f"{PATTERN.SPACE_PUNCT}+", '_', var_txt.lower()).strip('_')

        if re.match(r"[0-9]", var_txt):
            var_name = f"var_{var_name}"

        exists = [name for name in self._registry.keys() if
                  re.fullmatch(f"{var_name}(_[0-9]+)?", name)]

        # First occurrence of this base name
        if not exists:
            self._registry[var_name] = value
            return var_name

        # If the var name already maps to the same value, reuse it
        if self._registry.get(var_name) == value:
            return var_name

        # Otherwise, create a new unique name
        new_var_name = f"{var_name}_{len(exists)}"
        self._registry[new_var_name] = value
        return new_var_name

    def reset(self):
        """Clear all stored variable mappings."""
        self._registry.clear()


VAR_REGISTRY = VarRegistry()


class SeparatorNode(LineData):
    """
    Represents a category pattern for separators in grammar/text parsing.
    """

    def __init__(self, sep: str):
        """Initialize a SeparatorNode with the given separator."""
        super().__init__(sep)

    def to_regex(self) -> str:
        """Convert a category-separator data structure into a regex pattern."""
        raw = self.raw_data
        cleaned = raw.strip()

        # Always work with a Line object once
        line = text.Line(raw)

        # If there is meaningful content, build the pattern with optional leading/trailing spaces
        if cleaned:
            pattern_parts = [text.Line(cleaned).convert_to_regex_pattern()]

            if line.is_leading:
                pattern_parts.insert(0, r" *")

            if line.is_trailing:
                pattern_parts.append(r" *")

            return "".join(pattern_parts)

        # Fallback: empty or whitespace-only input
        return line.convert_to_regex_pattern()

    def to_template_snippet(self) -> str:
        """Generate a line textfsm snippet."""
        return f"{self.leading}{TextPattern(self.data)}{self.trailing}"


class SpacerNode(LineData):
    """
    Represents a category pattern for whitespace or spacer tokens in grammar/text parsing.
    """

    def __init__(self, is_empty: bool = False):
        """Initialize a SpacerNode with optional zero-space allowance."""
        super().__init__("")
        self.is_empty = is_empty

    def to_regex(self) -> str:
        """Convert the spacer configuration into a regex pattern."""
        return ' *' if self.is_empty else PATTERN.SPACES

    def to_template_snippet(self) -> str:
        """Generate a template snippet for the spacer."""
        return "optional_spaces()" if self.is_empty else "  "


class LeftDataNode(LineData):
    """
    Represents a category pattern for left‑aligned data in grammar/text parsing.
    """

    def __init__(self, data: str):
        """Initialize a LeftDataNode with the given raw data string."""
        super().__init__(data)

    def to_regex(self) -> str:
        """Convert raw data into a regex pattern."""
        return TextPattern(self.raw_data)

    def to_template_snippet(self) -> str:
        """Generate a template snippet for the raw data."""
        return self.raw_data


class RightDataNode(LineData):
    """
    Represents a category pattern for right‑aligned data in grammar/text parsing.
    """

    def __init__(self, data: str, var_txt: str):
        """Initialize a RightDataNode with raw data and variable text."""
        super().__init__(data)
        # self.var_name = re.sub(f"{PATTERN.SPACE_PUNCT}+", '_', var_txt.lower()).strip('_')
        self.var_name = VAR_REGISTRY.assign(var_txt, data)

    @property
    def is_empty(self) -> bool: return self.data == ""

    def to_regex(self) -> str:
        """Convert the data into a regex pattern."""
        if self.data:
            translator = PatternTranslator.do_factory_create(self.data)
            return translator.get_regex_pattern(var=self.var_name)
        return f"(?P<{self.var_name}>.*|)"

    def to_template_snippet(self):
        if self.data:
            translator = PatternTranslator.do_factory_create(self.data, multiple=True)
            snippet = translator.get_template_snippet(var=self.var_name)
            if re.sub(r"[ \r\n]+", "", self.leading):
                snippet = f"wss(){snippet}"
            if re.sub(r"[ \r\n]+", "", self.trailing):
                snippet = f"{snippet}wss()"
            return snippet
        return f"anything(var_{self.var_name}, or_empty)"


class CategoryLineTranslator(LineData):
    """
    Represents a category pattern for parsing a line of text into
    left data, separator, and right data components.
    """
    def __init__(self, line: str, count: int = 1, separator: str = ":"):
        super().__init__(line)

        # Parsing configuration
        self.count = count
        self.separator = separator

        # Parsed components
        self.left_data = ""
        self.right_data = ""

        # Internal Node List
        self._lst = []

        self.process()

    def __bool__(self) -> bool: return True if self._lst else False

    def __len__(self) -> int: return len(self._lst)

    @property
    def parsed(self) -> bool:
        """
        Indicate whether parsing produced any category pattern nodes.
        """
        return bool(self)

    def to_regex(self) -> str:
        """
        Convert the parsed line into a regex pattern.
        """
        optional_spaces_pat = ' *'
        result: list[str] = [
            optional_spaces_pat if self.is_leading else ""]
        prev_item, is_last_item_empty, item = None, False, None

        for item in self._lst:
            pat = item.to_regex()
            if (
                isinstance(item, RightDataNode) and
                item.is_empty and prev_item and not prev_item.is_trailing
            ):
                pat = f"{optional_spaces_pat}{pat}"
            result.append(pat)
            prev_item = item
        else:
            if isinstance(item, RightDataNode) and item.is_empty:
                is_last_item_empty = True

        if is_last_item_empty:
            result.append(
                optional_spaces_pat if self.is_trailing else "")

        pattern = "".join(result)
        replaced_pat = r"( +)(anything[\(]var_\w+, or_empty[\)])"
        return re.sub(replaced_pat, r"optional_spaces()\2", pattern)

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet string from parsed nodes.
        """
        result: list[str] = [self.leading]
        prev_item, is_last_item_empty, item = None, False, None

        for item in self._lst:
            snippet = item.to_template_snippet()
            if (
                isinstance(item, SpacerNode) and
                isinstance(prev_item, RightDataNode) and
                prev_item.to_template_snippet().endswith("wss()")
            ):
                continue

            if (
                isinstance(item, RightDataNode) and
                item.is_empty and prev_item and not prev_item.is_trailing
            ):
                snippet = f"optional_spaces(){snippet}"
            result.append(snippet)
            prev_item = item
        else:
            if isinstance(item, RightDataNode) and item.is_empty:
                is_last_item_empty = True

        if is_last_item_empty:
            result.append(self.trailing)

        tmpl_snippet = "".join(result)
        replaced_pat = r"( +)(anything[\(]var_\w+, or_empty[\)])"
        return re.sub(replaced_pat, r"optional_spaces()\2", tmpl_snippet)

    def scan_to_boundary(self, char_pos: int, direction: str = "right") -> int:
        """
        Find the nearest non-space character position in the given direction.
        """
        if self.data[char_pos] == " ":
            return char_pos

        step = 1 if direction == "right" else -1
        total = len(self.data)

        i = j = char_pos
        while 0 <= i < total:
            if self.data[i] == " ":
                return j
            j = i
            i += step

        return j

    def word_at(self, char_pos: int) -> str:
        """
        Extract the word at the given character position.
        """

        most_right_pos = self.scan_to_boundary(char_pos, direction='right')
        most_left_pos = self.scan_to_boundary(char_pos, direction='left')

        word = self.data[most_left_pos:most_right_pos]
        return word

    def split_components(self) -> tuple[str, str, str]:
        """
        Split the line into left, separator, and right segments.
        """
        left_raw, right_raw = self.data.split(self.separator, maxsplit=1)
        left_node, right_node = LineData(left_raw), LineData(right_raw)

        left = f"{left_node.leading}{left_node.data}"
        separator = f"{left_node.trailing}{self.separator}{right_node.leading}"
        right = f"{right_node.data}{right_node.trailing}"

        return left, separator, right

    def validate_category_pattern(self) -> None:
        """Ensure the line contains a valid category pattern."""
        if self.separator not in self.data:
            self.raise_runtime_error(
                msg=f"Missing separator '{self.separator}' in data."
            )

        index = self.data.index(self.separator)
        if index == 0:
            self.raise_runtime_error(
                msg=f"No variable text before separator '{self.separator}'."
            )

        chk_word = self.word_at(index)
        if self.is_time_ipv6_or_mac_format(chk_word):
            self.raise_runtime_error(
                msg=f"Unsupported variable text format detected: '{chk_word}'."
            )

    @classmethod
    def is_like_time_ipv6_or_mac(cls, data: str) -> bool:
        """
        Determine whether the given string resembles a time, IPv6, or MAC address format.
        """
        mac_pat = r"[a-f\d]{1,2}(?::[a-f\d]{1,2}){2,5}"
        ipv6_pat = r"[a-f\d]{1,4}(?::([a-f\d]{1,4})?)+:[a-f\d]{1,4}"

        is_time = bool(re.search(r"\d+(?::\d+)+", data))
        is_mac_addr = bool(re.match(mac_pat, data, re.I))
        is_ipv6 = (
                data.endswith("::")
                or data.startswith("::")
                or bool(re.match(ipv6_pat, data, re.I))
        )

        return is_time or is_mac_addr or is_ipv6

    def is_time_ipv6_or_mac_format(self, data: str) -> bool:
        """
        Instance-level wrapper for `is_time_or_ipv6_mac_format`.
        """
        return self.is_like_time_ipv6_or_mac(data)

    def extract_next_value(self) -> tuple[str, str]:
        """
        Attempt to extract a value and remaining string from right data.
        """
        mult_space_pat = '  +'
        spaces_pat = PATTERN.SPACES
        double_spaces = "  "

        next_count = self.count - 1
        if not next_count or not self.right_data.strip():
            return self.right_data, ""

        try:
            # Attempt recursive parsing
            node = self(self.right_data, count=next_count,
                        separator=self.separator)
            left_data = node.left_data

            if left_data.strip() and re.search(r"\s{2,}", left_data):
                parts = utils.split_by_matches(left_data, r"\s{2,}")
                val = "".join(parts[:-1])
                return val, self.right_data[len(val):]

            if left_data.strip() and re.search(r"\s+", left_data):
                parts = utils.split_by_matches(left_data, r"\s+")
                val = "".join(parts[:-1])
                return val, self.right_data[len(val):]

            return "", self.right_data

        except Exception:     # noqa
            # Fallback parsing logic
            items = re.split(spaces_pat, self.right_data)
            parts: list[str] = []

            for item in items:
                is_separator = item == self.separator
                is_valid = (
                        not self.is_time_ipv6_or_mac_format(item)
                        and item.endswith(self.separator)
                )
                parts.append(TextPattern(item))
                if is_separator and is_valid:
                    break

            pattern = spaces_pat.join(parts)
            match = re.search(pattern, self.right_data)
            left_chunk = match.group()
            remaining = self.right_data[len(left_chunk):]

            if double_spaces in left_chunk:
                first, last = re.split(mult_space_pat, left_chunk, maxsplit=1)
                return first, f"{last}{remaining}"

            # Secondary fallback: stop at time/IPv6/MAC formats
            parts.clear()
            for item in items:
                parts.append(item)
                if self.is_time_ipv6_or_mac_format(item):
                    break

            pattern = spaces_pat.join(parts)
            match = re.search(pattern, self.right_data)
            left_chunk = match.group()
            remaining = self.right_data[len(left_chunk):]
            return left_chunk, remaining

    def process(self) -> None:
        """
        Parse the input line into category pattern nodes.
        """
        if not self.count:
            return

        self.validate_category_pattern()

        left_text, whole_sep, remaining = self.split_components()
        self.left_data = left_text
        self.right_data = remaining

        # Append left data and separator nodes
        self._lst.append(LeftDataNode(left_text))
        self._lst.append(SeparatorNode(whole_sep))

        # Append right data node
        val, remainder = self.extract_next_value()
        self._lst.append(RightDataNode(val, left_text))

        # Recursively parse remaining data if present
        if remainder:
            try:
                other_node = self(remainder, count=self.count - 1)
                if other_node.parsed:
                    self._lst.append(SpacerNode())
                    self._lst.append(other_node)
            except Exception:   # noqa
                return


class CategoryLinesTranslator(RuntimeException):
    """
    Represent and process multiple lines into category pattern nodes.
    """

    def __init__(
        self,
        *lines: list[str],
        options: Optional[dict | None] = None,
        count: int = 1,
        separator: str = ":",
        starting_from: Optional[str | int | None] = None,
        ending_at: Optional[str | int | None] = None,
    ):
        # Normalized input
        self.lines = text.get_list_of_lines(*lines)

        # Parsing configuration
        self.options = options or dict()
        self.count = count
        self.separator = separator
        self.kwargs = dict(count=self.count, separator=self.separator)

        # Range selection
        self.starting_from = starting_from
        self.ending_at = ending_at
        self.start_index: Optional[int | None] = None
        self.end_index: Optional[int | None] = None

        # Parsed nodes
        self._lst: list = []

        VAR_REGISTRY.reset()

        self.process()

    @property
    def is_category_format(self) -> bool:
        """
        Check whether any parsed node is a CategoryLineTranslator.
        """
        return any(isinstance(item, CategoryLineTranslator) for item in self._lst)

    def __bool__(self) -> bool: return True if self._lst else False

    def __len__(self) -> int: return len(self._lst)

    def process(self) -> None:
        """
        Parse the input lines into category pattern nodes.
        """
        self.start_index = get_line_position_by(self.lines, self.starting_from)
        self.end_index = get_line_position_by(self.lines, self.ending_at)

        if self.start_index and self.end_index and self.start_index >= self.end_index:
            self.end_index = None

        start_index = self.start_index + 1 if self.start_index is not None else self.start_index
        lines = self.lines[start_index:self.end_index]

        for index, line in enumerate(lines):
            try:
                kwargs = self.options.get(str(index), self.kwargs)
                node = CategoryLineTranslator(line, **kwargs)
                self._lst.append(node if node.parsed else line)
            except Exception:  # noqa
                self._lst.append(line)

    def validate_category_format(self) -> None:
        """Raise an error if the parsed lines are not in category format."""
        if not self.is_category_format:
            self.raise_runtime_error(msg="Text is not in category format.")

    def to_regex(self) -> str:
        """
        Convert the parsed lines into a regex pattern.
        """
        self.validate_category_format()

        result: list[str] = []
        for item in self._lst:
            is_category_line_pat = isinstance(item, CategoryLineTranslator)
            result.append(item.to_regex() if is_category_line_pat else TextPattern(item))

        return str.join(f"({PATTERN_CRNL})", result)

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet string from parsed lines.
        """
        self.validate_category_format()

        result: list[str] = [
            item.to_template_snippet() if isinstance(item, CategoryLineTranslator) else item
            for item in self._lst
        ]

        tmpl_snippet = text.join_string(*result, separator="\n")

        if self.start_index is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.start_index)
            tmpl_snippet = f"{line_snippet} -> Table\nTable\n{tmpl_snippet}"

        if self.end_index is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.end_index)
            tmpl_snippet = f"{tmpl_snippet}\n{line_snippet} -> EOF"

        return tmpl_snippet
