"""
textfsmgen.gpcategory
=====================

Provides category definitions and grouping utilities for grammar patterns
used in the TextFSM Generator framework. This module centralizes the
classification of grammar pattern categories, ensuring consistent handling
across parsing, translation, and validation workflows.

Purpose
-------
- Define semantic categories for grammar patterns.
- Support category‑specific validation rules and translation logic.
- Improve readability and maintainability of generated FSM templates.
- Enable interoperability across CLI, GUI, and test modules.
"""

import re

from textfsmgen.deps import regexapp_TextPattern as TextPattern
from textfsmgen.deps import genericlib_NUMBER as NUMBER     # noqa
from textfsmgen.deps import genericlib_STRING as STRING     # noqa
from textfsmgen.deps import genericlib_PATTERN as PATTERN   # noqa
from textfsmgen.deps import genericlib_text_module as text

from textfsmgen.gp import LData, TranslatedPattern
from textfsmgen.exceptions import RuntimeException
from textfsmgen.gpiterative import IterativeLinePattern

from textfsmgen.gpcommon import get_line_position_by
from textfsmgen.gpcommon import get_fixed_line_snippet


class BaseCategoryPattern(LData):
    """
    BaseCategoryPattern
    -------------------
    Abstract base class for all grammar/text parsing category patterns.
    Extends `LData` to provide a common interface and shared behavior
    for specialized category pattern classes.

    Notes
    -----
    - This class is not intended to be used directly.
    - Subclasses such as `CategorySepPattern`, `CategoryLeftDataPattern`,
      and `CategoryRightDataPattern` implement specific parsing logic.
    - Provides a consistent foundation for regex conversion and
      template snippet generation across categories.
    """


class CategorySepPattern(BaseCategoryPattern):
    """
    CategorySepPattern
    ------------------
    Represents a category pattern for separators in grammar/text parsing.
    This class extends `BaseCategoryPattern` to handle separator tokens,
    providing both regex conversion and template snippet generation.

    Parameters
    ----------
    sep : str
        The separator string used to initialize the category pattern.
    """

    def __init__(self, sep: str):
        """Initialize a CategorySepPattern with the given separator."""
        super().__init__(sep)

    def to_regex(self) -> str:
        """
        Convert category-separator data structure into a regex pattern.

        Returns
        -------
        str
            A regex pattern string representing the separator.
        """
        node = IterativeLinePattern(self.raw_data)
        return node.to_regex()

    def to_template_snippet(self) -> str:
        """
        Generate a line textfsm snippet.

        Returns
        -------
        str
            A formatted template snippet string consisting of
            leading context, separator data, and trailing context.
        """
        return f"{self.leading}{TextPattern(self.data)}{self.trailing}"


class CategorySpacerPattern(BaseCategoryPattern):
    """
    CategorySpacerPattern
    ---------------------
    Represents a category pattern for whitespace or spacer tokens in grammar/text parsing.
    This class extends `BaseCategoryPattern` to handle cases where a separator may be
    empty, a single space, or multiple spaces.

    Parameters
    ----------
    is_empty : bool, optional
        Flag indicating whether the spacer should allow zero spaces.
        Defaults to False.
    """

    def __init__(self, is_empty: bool = False):
        """Initialize a CategorySpacerPattern with optional zero-space allowance."""
        super().__init__(STRING.EMPTY)
        self.is_empty = is_empty

    def to_regex(self) -> str:
        """
        Convert the spacer configuration into a regex pattern.

        Returns
        -------
        str
            Regex pattern string for zero-or-more spaces if `is_empty` is True,
            otherwise for one-or-more spaces.
        """
        return PATTERN.ZOSPACES if self.is_empty else PATTERN.SPACES

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet for the spacer.

        Returns
        -------
        str
            `'zero_or_spaces()'` if `is_empty` is True,
            otherwise `STRING.DOUBLE_SPACES`.
        """
        return "zero_or_spaces()" if self.is_empty else STRING.DOUBLE_SPACES


class CategoryLeftDataPattern(BaseCategoryPattern):
    """
    CategoryLeftDataPattern
    -----------------------
    Represents a category pattern for left‑aligned data in grammar/text parsing.
    This class extends `BaseCategoryPattern` to handle raw data tokens that
    are preserved as-is for regex conversion and template snippet generation.

    Parameters
    ----------
    data : str
        The raw data string used to initialize the category pattern.
    """

    def __init__(self, data: str):
        """Initialize a CategoryLeftDataPattern with the given raw data string."""
        super().__init__(data)

    def to_regex(self) -> str:
        """
        Convert raw data into a regex pattern.

        Returns
        -------
        str
            A regex pattern string representing the raw data.
        """
        return TextPattern(self.raw_data)

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet for the raw data.

        Returns
        -------
        str
            The raw data string, unchanged.
        """
        return self.raw_data


class CategoryRightDataPattern(BaseCategoryPattern):
    """
    CategoryRightDataPattern
    ------------------------
    Represents a category pattern for right‑aligned data in grammar/text parsing.
    This class extends `BaseCategoryPattern` to handle raw data tokens that
    may be associated with a variable name. It supports regex conversion and
    template snippet generation, even when the data is empty.

    Parameters
    ----------
    data : str
        The raw data string used to initialize the category pattern.
    var_txt : str
        The variable text used to derive a sanitized variable name.
    """

    def __init__(self, data: str, var_txt: str):
        """Initialize a CategoryRightDataPattern with raw data and variable text."""
        super().__init__(data)
        symbol_n_space_pat = '[ %s' % PATTERN.PUNCTS[NUMBER.ONE:]
        self.var_name = re.sub(symbol_n_space_pat, '_', var_txt).strip('_')

    @property
    def is_empty(self) -> bool:
        """
        Check if the data string is empty.

        Returns
        -------
        bool
            True if the data string equals `STRING.EMPTY`, False otherwise.
        """
        return self.data == STRING.EMPTY

    def to_regex(self) -> str:
        """
        Convert the data into a regex pattern.

        Returns
        -------
        str
            Regex pattern string. If data is provided, uses a translated
            pattern with the variable name. If empty, returns a generic
            named group pattern.
        """
        if self.data:
            pat_obj = TranslatedPattern.do_factory_create(self.data)
            return pat_obj.get_regex_pattern(var=self.var_name)
        return f"(?P<{self.var_name}>.*|)"

    def to_template_snippet(self):
        if self.data:
            pat_obj = TranslatedPattern.do_factory_create(self.data)
            return pat_obj.get_template_snippet(var=self.var_name)
        return f"something(var_{self.var_name}, or_empty)"


class CategoryLinePattern(BaseCategoryPattern):
    """
    CategoryLinePattern
    -------------------
    Represents a category pattern for parsing a line of text into
    left data, separator, and right data components. This class
    extends `BaseCategoryPattern` to support recursive parsing,
    regex conversion, and template snippet generation.

    Parameters
    ----------
    line : str
        The input line string to be parsed.
    count : int, optional
        Number of recursive parsing attempts. Defaults to 1.
    separator : str, optional
        Separator character used to split the line. Defaults to ':'.

    Attributes
    ----------
    count : int
        Number of recursive parsing attempts.
    separator : str
        Separator character used to split the line.
    left_data : str
        Parsed left-hand data segment.
    right_data : str
        Parsed right-hand data segment.
    _lst : list
        Internal list of parsed category pattern nodes.
    """
    def __init__(self, line: str, count: int = 1, separator: str = ":"):
        super().__init__(line)
        self.count = count
        self.separator = separator
        self.left_data = STRING.EMPTY
        self.right_data = STRING.EMPTY
        self._lst = []
        self.process()

    def __len__(self) -> int:
        """
        Return the number of parsed category pattern nodes.

        This method provides the length of the internal list `_lst`,
        which stores the parsed nodes generated during processing.

        Returns
        -------
        int
            The number of parsed nodes contained in the internal list.

        Notes
        -----
        - Equivalent to calling ``len(self._lst)``.
        - Useful for quickly checking how many nodes were parsed from
          the input line.
        """
        return len(self._lst)

    @property
    def parsed(self) -> bool:
        """
        Indicate whether parsing produced any category pattern nodes.

        This property evaluates the truthiness of the object, which is
        determined by the presence of parsed nodes in the internal list.

        Returns
        -------
        bool
            True if parsing produced one or more nodes, False otherwise.

        Notes
        -----
        - Relies on the `__bool__` or `__len__` implementation of the class.
        - Useful for quickly checking whether parsing was successful.
        """
        return bool(self)

    def to_regex(self) -> str:
        """
        Convert the parsed line into a regex pattern.

        This method constructs a regex pattern by iterating over parsed
        category pattern nodes. It handles special cases where right-hand
        data patterns may be empty, ensuring that optional spacing is
        represented correctly in the final regex.

        Returns
        -------
        str
            A regex pattern string representing the parsed line.

        Notes
        -----
        - If a `CategoryRightDataPattern` is empty and follows a non-trailing
          item, the pattern is prefixed with `zero_or_spaces_pattern`.
        - If the last item is an empty `CategoryRightDataPattern`, trailing
          optional spaces are appended.
        - Regex substitution ensures that redundant space + placeholder
          patterns are normalized into `zero_or_spaces()`.
        """
        zero_or_spaces_pat = PATTERN.ZOSPACES
        result: list[str] = [
            zero_or_spaces_pat if self.is_leading else STRING.EMPTY]
        prev_item, is_last_item_empty, item = None, False, None

        for item in self._lst:
            pat = item.to_regex()
            if (
                isinstance(item, CategoryRightDataPattern) and
                item.is_empty and prev_item and not prev_item.is_trailing
            ):
                pat = f"{zero_or_spaces_pat}{pat}"
            result.append(pat)
            prev_item = item
        else:
            if isinstance(item, CategoryRightDataPattern) and item.is_empty:
                is_last_item_empty = True

        if is_last_item_empty:
            result.append(
                zero_or_spaces_pat if self.is_trailing else STRING.EMPTY)

        pattern = STRING.EMPTY.join(result)
        replaced_pat = r"( +)(something[\(]var_\w+, or_empty[\)])"
        return re.sub(replaced_pat, r"zero_or_spaces()\2", pattern)

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet string from parsed nodes.

        This method constructs a template snippet by iterating over parsed
        category pattern nodes. It handles special cases where right-hand
        data patterns may be empty, ensuring that optional spacing is
        represented correctly in the snippet.

        Returns
        -------
        str
            A formatted template snippet string representing the parsed line.

        Notes
        -----
        - If a `CategoryRightDataPattern` is empty and follows a non-trailing
          item, the snippet is prefixed with `zero_or_spaces()`.
        - If the last item is an empty `CategoryRightDataPattern`, the trailing
          context is appended.
        - Regex substitution ensures that redundant space + placeholder patterns
          are normalized into `zero_or_spaces()`.
        """
        result: list[str] = [self.leading]
        prev_item, is_last_item_empty, item = None, False, None

        for item in self._lst:
            snippet = item.to_template_snippet()
            if (
                isinstance(item, CategoryRightDataPattern) and
                item.is_empty and prev_item and not prev_item.is_trailing
            ):
                snippet = f"zero_or_spaces(){snippet}"
            result.append(snippet)
            prev_item = item
        else:
            if isinstance(item, CategoryRightDataPattern) and item.is_empty:
                is_last_item_empty = True

        if is_last_item_empty:
            result.append(self.trailing)

        tmpl_snippet = STRING.EMPTY.join(result)
        replaced_pat = r"( +)(something[\(]var_\w+, or_empty[\)])"
        return re.sub(replaced_pat, r"zero_or_spaces()\2", tmpl_snippet)

    def get_remaining_chars_by_pos(self, char_pos: int,
                                   direction: str = "right") -> int:
        """
        Find the nearest non-space character position in the given direction.

        This method scans the string starting from the given character position
        and moves either left or right until a space character is encountered.
        It returns the position of the last non-space character before the space.

        Parameters
        ----------
        char_pos : int
            The character index within `self.data` from which to begin scanning.
        direction : str, optional
            Direction to search, either "right" or "left". Defaults to "right".

        Returns
        -------
        int
            The index of the nearest non-space character before a space in the
            specified direction. If the starting position is already a space,
            returns `char_pos`.

        Notes
        -----
        - The search stops when a space character is found or the bounds of
          the string are reached.
        - Useful for determining word boundaries in parsing operations.
        """
        blank_space = STRING.SPACE_CHAR

        if self.data[char_pos] == blank_space:
            return char_pos

        total = len(self.data)
        i = j = char_pos

        while NUMBER.ZERO <= i < total:
            if self.data[i] == blank_space:
                return j
            j = i
            i = i + NUMBER.ONE if direction == "right" else i - NUMBER.ONE

        return j

    def get_word_by_pos(self, char_pos: int) -> str:
        """
        Extract the word at the given character position.

        This method identifies the boundaries of a word in the input string
        by scanning left and right from the specified character position until
        a space character is encountered. It then returns the substring
        representing the word.

        Parameters
        ----------
        char_pos : int
            The character index within `self.data` from which to extract the word.

        Returns
        -------
        str
            The word containing the character at the given position.

        Notes
        -----
        - Word boundaries are determined by space characters.
        - Leading and trailing spaces are excluded from the returned word.
        - If `char_pos` points to a space, the nearest word boundaries are used.
        """

        most_right_pos = self.get_remaining_chars_by_pos(char_pos, direction='right')
        most_left_pos = self.get_remaining_chars_by_pos(char_pos, direction='left')

        word = self.data[most_left_pos:most_right_pos]
        return word

    def get_triple_by_separator(self) -> tuple[str, str, str]:
        """
        Split the line into left, separator, and right segments.

        This method divides the input line into three parts:
        - The left-hand data segment
        - The separator string (including surrounding whitespace)
        - The right-hand data segment

        It uses `LData` wrappers to normalize whitespace handling
        around the separator and ensures leading/trailing spaces
        are preserved in the correct segment.

        Returns
        -------
        tuple[str, str, str]
            A tuple containing:
            - left : str
                The left-hand data segment with leading whitespace.
            - separator : str
                The separator string with surrounding whitespace.
            - right : str
                The right-hand data segment with trailing whitespace.
        """
        v1, v2 = self.data.split(self.separator, maxsplit=1)
        node1, node2 = LData(v1), LData(v2)

        left = f"{node1.leading}{node1.data}"
        separator = f"{node1.trailing}{self.separator}{node2.leading}"
        right = f"{node2.data}{node2.trailing}"

        return left, separator, right

    def raise_exception_if_not_category_pattern(self) -> None:
        """
        Validate that the line contains a valid category pattern.

        This method ensures that the input line adheres to the expected
        category pattern structure. It checks for the presence of a separator,
        verifies that variable text exists before the separator, and rejects
        unsupported formats such as time, IPv6, or MAC address patterns.

        Raises
        ------
        RuntimeError
            If the line does not contain the expected separator.
        RuntimeError
            If variable text is missing before the separator.
        RuntimeError
            If the variable text format is unsupported (time, IPv6, or MAC address).
        """
        if self.separator not in self.data:
            self.raise_runtime_error(
                msg=f"Data string does not contain the expected separator '{self.separator}'."
            )

        index = self.data.index(self.separator)
        if index == NUMBER.ZERO:
            self.raise_runtime_error(
                msg=f"Data string is missing variable text before separator '{self.separator}'."
            )

        chk_word = self.get_word_by_pos(index)
        if self.is_time_ipv6_or_mac_addr_format(chk_word):
            self.raise_runtime_error(
                msg=f"Unsupported variable text format detected: '{chk_word}'."
            )

    @classmethod
    def is_time_or_ipv6_mac_format(cls, data: str) -> bool:
        """
        Determine whether the given string resembles a time, IPv6, or MAC address format.

        Parameters
        ----------
        data : str
            The input string to evaluate.

        Returns
        -------
        bool
            True if the string matches a time format (e.g., "12:34:56"),
            a MAC address format (e.g., "aa:bb:cc:dd:ee:ff"),
            or an IPv6 address format (e.g., "2001:0db8::1").
            False otherwise.

        Notes
        -----
        - Time format is detected by the presence of digits separated by colons.
        - MAC address format is detected by 1–2 hex digits separated by colons.
        - IPv6 format is detected by standard colon‑separated hex groups,
          including shorthand "::" notation.
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

    def is_time_ipv6_or_mac_addr_format(self, data: str) -> bool:
        """
        Instance-level wrapper for `is_time_or_ipv6_mac_format`.

        Parameters
        ----------
        data : str
            The input string to evaluate.

        Returns
        -------
        bool
            True if the string resembles a time, IPv6, or MAC address format.
        """
        return self.is_time_or_ipv6_mac_format(data)

    def try_to_get_value(self) -> tuple[str, str]:
        """
        Attempt to extract a value and remaining string from right data.

        This method tries to parse the `right_data` segment into a value and
        remaining string. It first attempts recursive parsing based on `count`,
        then falls back to a more lenient parsing strategy if an exception occurs.

        Returns
        -------
        tuple[str, str]
            A tuple containing:
            - The extracted value (str)
            - The remaining string (str)

        Notes
        -----
        - If `count` is zero or `right_data` is empty, returns `(right_data, "")`.
        - Uses stricter parsing first, then falls back to a more tolerant
          regex-based approach.
        - Handles special cases for time, IPv6, and MAC address formats.
        """
        at_least_one_spaces_pat = PATTERN.ATLONESPACES
        spaces_pat = PATTERN.SPACES
        double_spaces = STRING.DOUBLE_SPACES
        blank_space = STRING.SPACE_CHAR

        next_count = self.count - NUMBER.ONE
        if not next_count or not self.right_data.strip():
            return self.right_data, STRING.EMPTY

        try:
            # Attempt recursive parsing
            node = self(self.right_data, count=next_count,
                        separator=self.separator)
            left_data = node.left_data
            pat = at_least_one_spaces_pat if double_spaces in left_data else spaces_pat

            if blank_space in left_data:
                val, remaining = re.split(pat, self.right_data, maxsplit=1)
                return val, remaining
            return STRING.EMPTY, self.right_data

        except Exception:     # noqa
            # Fallback parsing logic
            items = re.split(spaces_pat, self.right_data)
            lst: list[str] = []

            for item in items:
                is_separator = item == self.separator
                is_valid = not self.is_time_ipv6_or_mac_addr_format(
                    item) and item.endswith(self.separator)
                lst.append(TextPattern(item))
                if is_separator and is_valid:
                    break

            other_pat = spaces_pat.join(lst)
            match = re.search(other_pat, self.right_data)
            other_left = match.group()
            other_remaining = self.right_data[len(other_left):]

            if double_spaces in other_left:
                other_first, other_last = re.split(at_least_one_spaces_pat,
                                                   other_left, maxsplit=1)
                return other_first, f"{other_last}{other_remaining}"

            # Secondary fallback: stop at time/IPv6/MAC formats
            lst.clear()
            for item in items:
                lst.append(item)
                if self.is_time_ipv6_or_mac_addr_format(item):
                    break

            other_pat = spaces_pat.join(lst)
            match = re.search(other_pat, self.right_data)
            other_left = match.group()
            other_remaining = self.right_data[len(other_left):]
            return other_left, other_remaining

    def process(self) -> None:
        """
        Parse the input line into category pattern nodes.

        This method orchestrates the parsing of a line into left data,
        separator, and right data components. It validates the input,
        extracts tokens, and constructs corresponding category pattern
        objects. Recursive parsing is supported when multiple separators
        are present.

        Notes
        -----
        - If `count` is zero, parsing is skipped.
        - Raises a runtime error if the line does not contain a valid
          category pattern.
        - Appends parsed nodes to the internal `_lst` list.

        Steps
        -----
        1. Validate that the line contains a valid category pattern.
        2. Split the line into left data, separator, and right data.
        3. Append `CategoryLeftDataPattern` and `CategorySepPattern` nodes.
        4. Attempt to extract a value from the right data.
        5. Append a `CategoryRightDataPattern` node.
        6. If additional data remains, recursively parse and append
           `CategorySpacerPattern` and nested `CategoryLinePattern`.

        Returns
        -------
        None
            This method modifies internal state (`self._lst`, `self.left_data`,
            `self.right_data`) but does not return a value.
        """
        if not self.count:
            return

        self.raise_exception_if_not_category_pattern()

        var_txt, whole_sep, remaining = self.get_triple_by_separator()
        self.left_data = var_txt
        self.right_data = remaining

        # Append left data and separator nodes
        self._lst.append(CategoryLeftDataPattern(var_txt))
        self._lst.append(CategorySepPattern(whole_sep))

        # Append right data node
        val, other_remaining = self.try_to_get_value()
        self._lst.append(CategoryRightDataPattern(val, var_txt))

        # Recursively parse remaining data if present
        if other_remaining:
            try:
                other_node = self(other_remaining, count=self.count - 1)
                if other_node.parsed:
                    self._lst.append(CategorySpacerPattern())
                    self._lst.append(other_node)
            except Exception:   # noqa
                return


class CategoryLinesPattern(RuntimeException):
    """
    Represent and process multiple lines into category pattern nodes.

    This class parses a sequence of input lines into category pattern
    structures. It supports optional start and end markers, configurable
    separators, and recursive parsing of individual lines.

    Parameters
    ----------
    *lines : Any
        One or more input lines to be parsed.
    options : dict, optional
        Mapping of line indices to keyword arguments for parsing.
        Defaults to an empty dictionary.
    count : int, optional
        Maximum recursion depth for parsing. Defaults to 1.
    separator : str, optional
        Separator string used to split lines. Defaults to ":".
    starting_from : str, optional
        Marker line indicating where parsing should begin.
    ending_to : str, optional
        Marker line indicating where parsing should end.

    Attributes
    ----------
    lines : list[str]
        Normalized list of input lines.
    options : dict
        Line-specific parsing options.
    count : int
        Recursion depth for parsing.
    separator : str
        Separator string used for splitting.
    kwargs : dict
        Default keyword arguments for line parsing.
    starting_from : str, int, or None, optional
        Start marker line.
    ending_to : str, int, or None, optional
        End marker line.
    index_a : int or None
        Index of the start marker line.
    index_b : int or None
        Index of the end marker line.
    _lst : list
        Parsed nodes or raw lines.
    """

    def __init__(
        self,
        *lines: list[str],
        options: dict | None = None,
        count: int = 1,
        separator: str = ":",
        starting_from: str | int | None = None,
        ending_to: str | int | None = None,
    ) -> None:
        self.lines = text.get_list_of_lines(*lines)
        self.options = options or dict()
        self.count = count
        self.separator = separator
        self.kwargs = dict(count=self.count, separator=self.separator)
        self.starting_from = starting_from
        self.ending_to = ending_to
        self.index_a: int | None = None
        self.index_b: int | None = None
        self._lst: list = []
        self.process()

    @property
    def is_category_format(self) -> bool:
        """
        Check whether any parsed node is a CategoryLinePattern.

        Returns
        -------
        bool
            True if at least one parsed node is a CategoryLinePattern,
            False otherwise.
        """
        return any(isinstance(item, CategoryLinePattern) for item in self._lst)

    def __len__(self) -> int:
        """
        Return the number of parsed nodes.

        Returns
        -------
        int
            The number of parsed nodes stored in `_lst`.
        """
        return len(self._lst)

    def process(self) -> None:
        """
        Parse the input lines into category pattern nodes.

        This method determines the start and end indices based on markers,
        then iterates through the relevant lines. Each line is parsed into
        a `CategoryLinePattern` if possible; otherwise, the raw line is
        preserved.

        Notes
        -----
        - If `starting_from` and `ending_to` markers overlap or are invalid,
          `ending_to` is ignored.
        - Errors during parsing fall back to storing the raw line.
        """
        self.index_a = get_line_position_by(self.lines, self.starting_from)
        self.index_b = get_line_position_by(self.lines, self.ending_to)

        if self.index_a and self.index_b and self.index_a >= self.index_b:
            self.index_b = None

        start_index = self.index_a + 1 if self.index_a is not None else self.index_a
        lines = self.lines[start_index:self.index_b]

        for index, line in enumerate(lines):
            try:
                kwargs = self.options.get(str(index), self.kwargs)
                node = CategoryLinePattern(line, **kwargs)
                self._lst.append(node if node.parsed else line)
            except Exception:  # noqa
                self._lst.append(line)

    def raise_exception_if_not_category_format(self) -> None:
        """
        Raise a runtime error if the parsed lines are not in category format.

        Raises
        ------
        RuntimeError
            If no `CategoryLinePattern` nodes are present.
        """
        if not self.is_category_format:
            self.raise_runtime_error(msg="Text is not in category format.")

    def to_regex(self) -> str:
        """
        Convert the parsed lines into a regex pattern.

        Returns
        -------
        str
            A regex pattern string representing the parsed lines.

        Raises
        ------
        RuntimeError
            If the lines are not in category format.
        """
        self.raise_exception_if_not_category_format()

        result: list[str] = []
        for item in self._lst:
            is_category_line_pat = isinstance(item, CategoryLinePattern)
            result.append(item.to_regex() if is_category_line_pat else TextPattern(item))

        return str.join(f"({PATTERN.CRNL})", result)

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet string from parsed lines.

        Returns
        -------
        str
            A formatted template snippet string representing the parsed lines.

        Raises
        ------
        RuntimeError
            If the lines are not in category format.
        """
        self.raise_exception_if_not_category_format()

        result: list[str] = [
            item.to_template_snippet() if isinstance(item, CategoryLinePattern) else item
            for item in self._lst
        ]

        tmpl_snippet = text.join_string(*result, separator=STRING.NEWLINE)

        if self.index_a is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.index_a)
            tmpl_snippet = f"{line_snippet} -> Table\nTable\n{tmpl_snippet}"

        if self.index_b is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.index_b)
            tmpl_snippet = f"{tmpl_snippet}\n{line_snippet} -> EOF"

        return tmpl_snippet
