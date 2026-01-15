"""
textfsmgen.gptabular
====================

Provides utilities for parsing tabular text into structured representations
that can be converted into regex patterns or template snippets.

Overview
--------
The `gptabular` module is part of the TextFSM Generator package. It focuses
on handling tabular text data where rows and columns are separated by
dividers, spaces, or fixed widths. The module abstracts the complexity of
parsing such text and exposes methods to generate:

* **Regex patterns** — for matching tabular rows in raw text.
* **Template snippets** — for building reusable parsing templates.

Key Features
------------
- Parse tabular text using:
  - Fixed column widths
  - Custom headers
  - Dividers (punctuation, spaces, multi-spaces, symbols)
- Validate and raise descriptive runtime errors when parsing fails.
- Convert parsed tables into:
  - Regex patterns (`to_regex`)
  - Template snippets (`to_template_snippet`)
- Support for flexible input formats and error handling.

Raises
------
RuntimeError
    If the provided text cannot be parsed into a valid tabular format.

Notes
-----
This module is intended to be used internally by the TextFSM Generator
framework, but can also be leveraged directly for advanced parsing tasks.
"""

from typing import List, Tuple, Dict, Optional, Any
from collections import Counter
import math
import statistics
import operator as op
import re

from textfsmgen.deps import regexapp_LinePattern as LinePattern
from textfsmgen.deps import genericlib_NUMBER as NUMBER     # noqa
from textfsmgen.deps import genericlib_STRING as STRING     # noqa
from textfsmgen.deps import genericlib_PATTERN as PATTERN   # noqa
from textfsmgen.deps import genericlib_INDEX as INDEX       # noqa
from textfsmgen.deps import genericlib_Misc as Misc
from textfsmgen.deps import genericlib_text_module as text
from textfsmgen.deps import genericlib_number_module as number

from textfsmgen.gp import TranslatedPattern
from textfsmgen.exceptions import RuntimeException

from textfsmgen.gpcommon import get_line_position_by
from textfsmgen.gpcommon import get_fixed_line_snippet


class TabularTextPattern(RuntimeException):
    """
    Represents a tabular text pattern that can be parsed into regex patterns
    or template snippets.

    This class provides functionality to:
    - Parse tabular text using dividers, fixed column widths, or headers.
    - Generate regex patterns for matching tabular rows.
    - Generate template snippets for building parsing templates.
    - Handle optional start and end markers within the text.

    Parameters
    ----------
    *lines : List[str]
        Input lines of text to be parsed.
    divider : str, optional
        Column divider character(s). Default is an empty string.
    columns_count : int, optional
        Expected number of columns. Default is 0.
    col_widths : list[int] or str, optional
        Column widths as a list of integers or a string of integers.
    header_names : list[str], optional
        Names of table headers.
    headers_data : list[str], optional
        Data for headers.
    custom_headers_data : str, optional
        Custom header data string.
    starting_from : str, optional
        Marker indicating where parsing should start.
    ending_to : str, optional
        Marker indicating where parsing should end.
    is_headers_row : bool, optional
        Whether the first row is a header row. Default is True.

    Raises
    ------
    RuntimeError
        If invalid column widths are provided or parsing fails.
    """
    def __init__(self, *lines, divider='', columns_count=0, col_widths=None,
                 header_names=None, headers_data=None, custom_headers_data='',
                 starting_from=None, ending_to=None,
                 is_headers_row=True):
        self.lines = text.get_list_of_lines(*lines)
        self.kwargs = dict(
            divider=divider,
            columns_count=columns_count,
            col_widths=col_widths or [],
            header_names=header_names,
            headers_data=headers_data,
            custom_headers_data=custom_headers_data,
            is_headers_row=is_headers_row
        )

        self.starting_from = starting_from
        self.ending_to = ending_to
        self.tabular_parser = None

        self.index_a = None
        self.index_b = None

        self.prepare_col_widths()
        self.process()

    def __len__(self) -> int:
        """Return 1 if a tabular parser exists, otherwise 0."""
        return int(bool(self.tabular_parser))

    def prepare_col_widths(self) -> None:
        """Validate and normalize column widths."""
        col_widths = self.kwargs.get("col_widths")
        if not col_widths:
            return

        normalized = []
        if text.is_string(col_widths) or Misc.is_list(col_widths):
            if text.is_string(col_widths):
                col_widths = col_widths.strip()
                widths = re.split(r"[ ,]+", col_widths)
            else:
                widths = col_widths[:]

            for idx, width_ in enumerate(widths):
                is_number, width = number.try_to_get_number(width_, return_type=int)
                if is_number:
                    normalized.append(width)
                elif idx == len(widths) - NUMBER.ONE:
                    normalized.append(STRING.EMPTY)
                else:
                    self.raise_runtime_error(
                        msg=(
                            f"Invalid column widths in {self.__class__.__name__}.\n"
                            "Expected: list of integers or string of integers\n"
                            f"Received: {col_widths!r}"
                        )
                    )

            self.kwargs.update(col_widths=normalized, columns_count=len(normalized))
        else:
            self.raise_runtime_error(
                msg=(
                    f"Invalid column widths in {self.__class__.__name__}.\n"
                    "Expected: list of integers or string of integers\n"
                    f"Received: {col_widths!r}"
                )
            )

    def process(self) -> None:
        """Initialize the tabular parser with the given lines and configuration."""
        self.index_a = get_line_position_by(self.lines, self.starting_from)
        self.index_b = get_line_position_by(self.lines, self.ending_to)

        lines = self.lines[self.index_a:self.index_b]
        self.tabular_parser = TabularTextPatternByVarColumns(*lines, **self.kwargs)

    def to_regex(self) -> str:
        """Return a regex pattern generated from the parsed table."""
        return self.tabular_parser.to_regex() if self else STRING.EMPTY

    def to_template_snippet(self) -> str:
        """Return a template snippet generated from the parsed table."""
        tmpl_snippet = (
            self.tabular_parser.to_template_snippet() if self else STRING.EMPTY
        )

        if not tmpl_snippet.strip():
            return tmpl_snippet

        lines = tmpl_snippet.splitlines()
        first_line = lines[0]

        # Handle starting marker
        if self.index_a is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.index_a)
            if line_snippet:
                if re.search(LinePattern(line_snippet), first_line):
                    tmpl_snippet = text.join_string(*lines[1:], separator="\n")
                tmpl_snippet = f"{line_snippet} -> Table\nTable\n{tmpl_snippet}"

        lines = tmpl_snippet.splitlines()
        last_line = lines[-1]

        # Handle ending marker
        if self.index_b is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.index_b)
            if line_snippet:
                if re.search(LinePattern(line_snippet), last_line):
                    tmpl_snippet = text.join_string(*lines[:-1], separator="\n")
                tmpl_snippet = f"{tmpl_snippet}\n{line_snippet} -> EOF"

        return tmpl_snippet


class TabularTextPatternByVarColumns(RuntimeException):
    """
    Parse tabular text with variable column structures and optional dividers.

    This class provides utilities to:
    - Detect whether lines start or end with a divider symbol.
    - Infer column counts if not explicitly provided.
    - Extract and normalize header data.
    - Generate reference rows based on different divider strategies
      (symbols, separators, or whitespace).
    - Produce default or header-derived variable names for columns.

    Parameters
    ----------
    *lines : List[str]
        Input lines representing tabular text.
    divider : str, optional
        Column divider character (default is empty string).
    columns_count : int, optional
        Number of columns. If not provided, inferred from content.
    col_widths : list[int] or str, optional
        Column widths as list of integers or string of integers.
    header_names : list[str] or str, optional
        Names of headers for columns.
    headers_data : list[str] or str, optional
        Raw header data, either as indices or substrings.
    custom_headers_data : str, optional
        Custom header information.
    is_headers_row : bool, optional
        Whether the first row is considered a header row (default True).
    **kwargs : dict
        Additional keyword arguments passed to downstream parsing.

    Attributes
    ----------
    lines : list[str]
        Normalized list of input lines.
    total_lines : int
        Number of lines in the input.
    divider : str
        Divider character used between columns.
    col_widths : list[int]
        Column widths.
    columns_count : int
        Number of columns.
    header_names : list[str]
        Names of headers for columns.
    headers_data : list[str]
        Raw header data.
    raw_headers_data : list[str]
        Processed header lines extracted from input.
    is_headers_row : bool
        Whether the first row is considered a header row.
    variables : list[str]
        Normalized variable names derived from headers.
    """

    def __init__(self, *lines, divider='', columns_count=0, col_widths=None,
                 header_names=None, headers_data=None, custom_headers_data='',
                 is_headers_row=True, **kwargs):
        self._is_start_with_divider = None
        self._is_end_with_divider = None

        self.lines = text.get_list_of_lines(*lines)
        self.total_lines = len(self.lines)
        self.divider = divider
        self.col_widths = col_widths or []
        self.columns_count = columns_count
        self.raise_exception_if_columns_count_not_provided()

        self.headers_data = headers_data
        self.custom_headers_data = custom_headers_data
        self.raw_headers_data = []
        self.header_names = header_names
        self.is_headers_row = is_headers_row
        self.variables = []

        self.kwargs = kwargs
        self.prepare_headers_data()

    def __len__(self):
        """Return True if columns_count is non-zero, else False."""
        return bool(self.columns_count)

    @property
    def is_divider_a_symbol(self):
        """Check if the divider is a punctuation symbol."""
        return bool(re.match(PATTERN.CHECK_PUNCT, self.divider))

    @property
    def is_start_with_divider(self):
        """Check if most lines start with the divider symbol."""
        if self._is_start_with_divider is None:
            if self.is_divider_a_symbol:
                count = sum(line.strip().startswith(self.divider) for line in self.lines)
                self._is_start_with_divider = op.gt(count, op.truediv(len(self.lines), NUMBER.TWO)) if count else False
            else:
                self._is_start_with_divider = False
        return self._is_start_with_divider

    @property
    def is_end_with_divider(self):
        """Check if most lines end with the divider symbol."""
        if self._is_end_with_divider is None:
            if self.is_divider_a_symbol:
                count = sum(line.strip().endswith(self.divider) for line in self.lines)
                self._is_end_with_divider = op.gt(count, op.truediv(len(self.lines), NUMBER.TWO)) if count else False
            else:
                self._is_end_with_divider = False
        return self._is_end_with_divider

    def raise_exception_if_columns_count_not_provided(self):
        """Infer column count from lines or raise error if zero."""
        pat = f"{PATTERN.PUNCTS_GROUP}$"
        for line in self.lines:
            if re.match(pat, line.strip()):
                self.columns_count = len(re.split(PATTERN.WHITESPACES, line.strip()))
                return
        if not self:
            self.raise_runtime_error(msg='columns_count cannot be zero')

    def prepare_headers_data(self):
        """Extract header lines from headers_data (indices or substrings)."""
        lst = self.raw_headers_data
        data = self.headers_data
        total_lines = len(self.lines)

        if text.is_string(data):
            pat = r' *[0-9]+([ ,]+[0-9]+)* *$'
            if re.match(pat, data):
                for index in map(int, re.split('[ ,]+', data)):
                    if index < total_lines:
                        hdr_line = self.lines[index]
                        if hdr_line not in lst:
                            lst.append(hdr_line)
            else:
                for sub_line in str.splitlines(data):
                    for line in self.lines:
                        if sub_line in line and line not in lst:
                            lst.append(line)

        elif Misc.is_list(data):
            for item in data:
                is_number, index = number.try_to_get_number(item, return_type=int)
                if is_number and index < total_lines:
                    hdr_line = self.lines[index]
                    if hdr_line not in lst:
                        lst.append(hdr_line)
                else:
                    for line in self.lines:
                        if item in line and line not in lst:
                            lst.append(line)

    def parse_headers_to_variables(self):
        """Normalize header names into valid variable identifiers."""
        variables = []
        header_names = self.header_names
        if not header_names:
            return variables

        if text.is_string(header_names):
            header_names = re.split('[ ,]+', header_names.strip())

        if Misc.is_list(header_names) and len(header_names) == self.columns_count:
            pat = '[ %s' % PATTERN.PUNCTS[1:]
            repl = STRING.UNDERSCORE_CHAR
            for i, hdr in enumerate(header_names):
                new_hdr = re.sub(pat, repl, hdr.strip())
                new_hdr = new_hdr if new_hdr == repl else new_hdr.rstrip(repl)
                variables.append(f"{new_hdr}{i}" if new_hdr in variables else new_hdr)

        return variables

    def get_default_variables(self):
        """Return default variable names as col0, col1, ..."""
        return [f"col{i}" for i in range(self.columns_count)]

    # -------------------------------
    # Reference row finders
    # -------------------------------

    def find_ref_row_by_symbols_divider(self, custom_line=''):
        """Find reference row using punctuation symbols as dividers."""
        fmt = ' *%(p)s( +%(p)s){%(rep)s} *$'
        pat = fmt % dict(p=PATTERN.PUNCTS, rep=self.columns_count - NUMBER.ONE)

        found_line = custom_line or next((line for line in self.lines if re.match(pat, line)), STRING.EMPTY)
        if not found_line:
            return None

        pattern = f' *{PATTERN.PUNCTS} *'
        return TabularRow.create_ref_row(found_line, pattern, case='findall', columns_count=self.columns_count)

    def find_ref_row_by_separator_divider(self, custom_line=''):
        """Find reference row using explicit separator divider."""
        fmt = ' *%(separator)s?(%(p)s%(separator)s){%(rep)s}%(p)s%(separator)s? *$'
        kwargs = dict(p=r'[^%s]+' % self.divider, rep=self.columns_count - NUMBER.ONE, separator=re.escape(self.divider))
        pat = fmt % kwargs

        found_line = custom_line or next((line for line in self.lines if re.match(pat, line)), STRING.EMPTY)
        if not found_line:
            return None

        return TabularRow.create_ref_row(found_line, self.divider, columns_count=self.columns_count, case='split')

    def find_ref_row_by_space_divider(self, spaces: str = ' ',
                                      custom_line: str = '') -> Optional['TabularRow']:
        """Find reference row using space or multi-space divider."""
        gap = STRING.EMPTY if spaces == STRING.SPACE_CHAR else STRING.SPACE_CHAR
        repetition = self.columns_count - NUMBER.ONE
        kwargs = dict(p=PATTERN.NON_WHITESPACES_OR_PHRASE, rep=repetition, gap=gap)
        pat = r' *%(p)s(%(gap)s +%(p)s){%(rep)s} *$' % kwargs

        found_line = custom_line or next((line for line in self.lines if re.match(pat, line)), None)
        if not found_line:
            return None

        # Build regex pattern for capturing columns
        lst = []
        fmt1 = '(?P<%(key)s>%(p)s%(gap)s +)'
        fmt2 = '(?P<%(key)s> *%(p)s%(gap)s +)'
        fmt3 = '(?P<%(key)s>%(p)s *)$'

        for index in range(self.columns_count):
            key = f'v{index:03d}'
            kwargs.update(key=key)
            fmt = fmt1 if index else fmt2
            lst.append(fmt % kwargs)
        lst[-NUMBER.ONE] = fmt3 % kwargs

        pattern = ''.join(lst)

        return TabularRow.create_ref_row(
            found_line, pattern,
            columns_count=self.columns_count,
            case='variable'
        )

    def find_ref_row_by_blank_space_divider(self) -> Optional['TabularRow']:
        """Find reference row using single space divider."""
        return self.find_ref_row_by_space_divider()

    def find_ref_row_by_multi_spaces_divider(self) -> Optional['TabularRow']:
        """Find reference row using multi-space divider."""
        return self.find_ref_row_by_space_divider(spaces='  ')

    def find_ref_row_by_custom_headers_line(self) -> Optional['TabularRow']:
        """Find reference row using custom header line."""
        return self.find_ref_row_by_symbols_divider(custom_line=self.custom_headers_data)

    def find_ref_row_by_col_widths(self, custom_line: str = '') -> Optional['TabularRow']:
        """Find reference row using fixed column widths."""
        lst = [
            f'(?P<v{index:03d}>.{{{width}}})' if index < self.columns_count - NUMBER.ONE
            else f'(?P<v{index:03d}>.*)'
            for index, width in enumerate(self.col_widths)
        ]
        pattern = text.join_string(*lst)

        found_line = custom_line or next((line for line in self.lines if re.match(pattern, line)), None)
        if not found_line:
            return None

        return TabularRow.create_ref_row(
            found_line, pattern,
            columns_count=self.columns_count,
            case='variable'
        )

    # -------------------------------
    # Table parsing
    # -------------------------------

    def try_to_get_table_by(self, case: str) -> Tuple[bool, Optional['TabularTable']]:
        """Attempt to parse table using the given case strategy."""
        methods = {
            "col_widths": self.find_ref_row_by_col_widths,
            "symbols": self.find_ref_row_by_symbols_divider,
            "separator": self.find_ref_row_by_separator_divider,
            "multi_spaces": self.find_ref_row_by_multi_spaces_divider,
            "blank_space": self.find_ref_row_by_blank_space_divider,
            "custom": self.find_ref_row_by_custom_headers_line,
        }
        ref_row = methods.get(case, self.find_ref_row_by_blank_space_divider)()
        if not ref_row:
            return False, None

        header_names = self.parse_headers_to_variables()
        table = TabularTable(
            *self.lines,
            ref_row=ref_row,
            divider=self.divider,
            header_names=header_names,
            raw_headers_data=self.raw_headers_data,
            is_start_with_divider=self._is_start_with_divider,
            is_end_with_divider=self._is_end_with_divider,
            is_headers_row=self.is_headers_row
        )
        return True, table

    def parse_table(self) -> 'TabularTable':
        """
        Parse the tabular text into a `TabularTable` object using the appropriate strategy.

        Returns
        -------
        TabularTable
            Parsed table object.

        Raises
        ------
        RuntimeException
            If parsing fails for the chosen strategy.
        """
        case, err_msg = STRING.EMPTY, STRING.EMPTY
        if self.col_widths:
            case = "col_widths"
            err_msg = (
                f"Parsing failed in {self.__class__.__name__}.\n"
                f"Case: {case}\n"
                "Reason: Unable to parse tabular text using fixed column widths."
            )
        elif re.match(f'{PATTERN.PUNCT}$', self.divider.strip()):
            case = "separator"
            err_msg = (
                f"Parsing failed in {self.__class__.__name__}.\n"
                f"Case: {case}\n"
                f"Reason: Unable to parse tabular text using divider {self.divider!r}."
            )
        elif self.custom_headers_data:
            case = "custom"
            err_msg = (
                f"Parsing failed in {self.__class__.__name__}.\n"
                f"Case: {case}\n"
                "Reason: Unable to parse tabular text using custom headers data."
            )
        elif self.divider == STRING.SPACE_CHAR:
            case = "blank_space"
            err_msg = (
                f"Parsing failed in {self.__class__.__name__}.\n"
                f"Case: {case}\n"
                "Reason: Unable to parse tabular text using blank space divider."
            )
        elif re.match('  +$', self.divider):
            case = "multi_spaces"
            err_msg = (
                f"Parsing failed in {self.__class__.__name__}.\n"
                f"Case: {case}\n"
                "Reason: Unable to parse tabular text using multi-space divider."
            )
        elif self.divider == STRING.EMPTY:
            case = "symbols"
            err_msg = (
                f"Parsing failed in {self.__class__.__name__}.\n"
                f"Case: {case}\n"
                "Reason: Unable to parse tabular text using empty/symbols divider."
            )
        else:
            self.raise_runtime_error(
                msg=(
                    f"Unsupported divider {self.divider!r} in {self.__class__.__name__}.\n"
                    "Hint: Provide a valid divider (e.g., space, multi-space, punctuation, or custom headers)."
                )
            )

        is_parsed, table = self.try_to_get_table_by(case)
        if not is_parsed:
            self.raise_runtime_error(msg=err_msg)

        return table


    def to_regex(self) -> str:
        """
        Convert parsed tabular text into a regex pattern.

        Returns
        -------
        str
            A regex pattern string generated from the parsed table.

        Raises
        ------
        RuntimeError
            If the provided text cannot be parsed into a tabular format.
        """
        table = self.parse_table()
        if not table:
            self.raise_runtime_error(
                msg=(
                    f"Unable to build regex pattern in {self.__class__.__name__}.\n"
                    "Reason: Provided text is not in a valid tabular format."
                )
            )
        return table.to_regex()

    def to_template_snippet(self) -> str:
        """
        Convert parsed tabular text into a template snippet.

        Returns
        -------
        str
            A template snippet string generated from the parsed table.

        Raises
        ------
        RuntimeError
            If the provided text cannot be parsed into a tabular format.
        """
        table = self.parse_table()
        if not table:
            self.raise_runtime_error(
                msg=(
                    f"Unable to build template snippet in {self.__class__.__name__}.\n"
                    "Reason: Provided text is not in a valid tabular format."
                )
            )
        return table.to_template_snippet()


class TabularTable(RuntimeException):
    """
    Represents a parsed tabular text structure with rows and columns.

    This class organizes tabular text into structured rows and columns,
    supports custom dividers, column widths, and header parsing, and
    provides utilities for alignment, cleaning, and conversion to dictionaries.

    Parameters
    ----------
    *lines : list[str]
        Input lines of tabular text.
    ref_row : TabularRow, optional
        Reference row used for parsing and alignment.
    divider : str, optional
        Column divider (space, punctuation, or custom symbol).
    col_widths : list[int], optional
        Fixed column widths for parsing.
    header_names : list[str], optional
        Names of table headers.
    raw_headers_data : list[str], optional
        Raw header data extracted from input.
    is_start_with_divider : bool, default=False
        Whether the table starts with a divider.
    is_end_with_divider : bool, default=False
        Whether the table ends with a divider.
    is_headers_row : bool, default=True
        Whether the first row is considered a header row.

    Attributes
    ----------
    rows : list[TabularRow]
        Parsed rows of the table.
    columns : list[TabularColumn]
        Parsed columns of the table.
    header_lines : list[str]
        Lines corresponding to headers.
    header_columns : list[TabularColumn]
        Columns corresponding to headers.
    first_column_data_info : dict
        Metadata about the first column (indices, spacers, values).
    last_column_data_info : dict
        Metadata about the last column (indices, spacers, values).
    """

    def __init__(self, *lines: str, ref_row: Optional['TabularRow'] = None,
                 divider: str = '', col_widths: Optional[List[int]] = None,
                 header_names: Optional[List[str]] = None,
                 raw_headers_data: Optional[List[str]] = None,
                 is_start_with_divider: bool = False,
                 is_end_with_divider: bool = False,
                 is_headers_row: bool = True) -> None:

        self.first_column_data_info: Dict[Any, Any] = {}
        self.last_column_data_info: Dict[Any, Any] = {}

        self.lines: List[str] = self.prepare_lines(lines)
        self.ref_row = ref_row
        self.divider: str = divider
        self.col_widths: Optional[List[int]] = col_widths

        self.rows: List['TabularRow'] = []
        self.columns: List['TabularColumn'] = []
        self.header_lines: List[str] = []
        self.header_columns: List['TabularColumn'] = []
        self.header_names: List[str] = header_names or []
        self.raw_headers_data: List[str] = raw_headers_data or []

        self._is_leading: Optional[bool] = None
        self._is_trailing: Optional[bool] = None

        self.is_start_with_divider: bool = is_start_with_divider
        self.is_end_with_divider: bool = is_end_with_divider
        self.is_headers_row: bool = is_headers_row

        self.is_divider: bool = bool(self.divider.strip())
        self.divider_snippet: str = f'zero_or_spaces(){re.escape(self.divider)}zero_or_spaces()'
        self.divider_leading_snippet: str = f'{re.escape(self.divider)}zero_or_spaces()'
        self.divider_trailing_snippet: str = f'zero_or_spaces(){re.escape(self.divider)}'

        self.process()

    def __len__(self) -> int:
        """Return 1 if table has rows and columns, else 0."""
        return int(bool(self.rows) and bool(self.columns))

    def __repr__(self) -> str:
        """Return a string representation of the table."""
        cls_name = Misc.get_instance_class_name(self)
        return f"{cls_name}(rows_count={len(self.rows)}, columns_count={len(self.columns)})"

    # -------------------------------
    # Properties
    # -------------------------------

    @property
    def is_leading(self) -> bool:
        """Check if the first column contains leading markers."""
        if self._is_leading is None:
            lst = []
            for cell in self.first_column.cells:
                if cell.text.strip():
                    lst.append(text.Line.has_leading(cell.data))
            for key, data in self.first_column_data_info.items():
                if isinstance(key, int):
                    lst.append(text.Line.has_leading(data))
            self._is_leading = any(lst)
        return self._is_leading

    @property
    def is_trailing(self) -> bool:
        """Check if any line contains trailing markers."""
        if self._is_trailing is None:
            for line in self.lines:
                self._is_trailing = text.Line.has_trailing(line)
                if self._is_trailing:
                    break
        return self._is_trailing

    @property
    def rows_count(self) -> int:
        """Return number of rows."""
        return len(self.rows)

    @property
    def columns_count(self) -> int:
        """Return number of columns."""
        return len(self.columns)

    @property
    def first_column(self) -> 'TabularColumn':
        """Return the first column."""
        return self.columns[INDEX.ZERO]

    @property
    def last_column(self) -> 'TabularColumn':
        """Return the last column."""
        return self.columns[-INDEX.ONE]

    # -------------------------------
    # Line preparation
    # -------------------------------

    def prepare_lines(self, lines: List[str]) -> List[str]:
        """
        Normalize and preprocess input lines, handling user markers.

        Parameters
        ----------
        lines : List[str]
            Raw input lines.

        Returns
        -------
        list[str]
            Processed lines ready for parsing.
        """

        def update_last_column_info(
                column_info: dict, line_: str, spacers_count_: int, baseline_: int
        ) -> None:
            """
            Inner helper for TabularTable.prepare_lines.

            Update metadata for the last column with line content and spacer information.
            """
            # Update list of data lines for the last column
            lst_data = column_info.setdefault("lst_data", [])
            lst_data.append(line_.lstrip())

            # Update spacer metadata
            spacers = column_info.setdefault("spacers", [])
            left_spacer = spacers_count_ - 6

            if not spacers:
                # Initialize spacers with left and baseline values
                spacers.extend(
                    [2 if left_spacer <= 0 else left_spacer, baseline_])
            else:
                # Adjust existing spacer values
                adjusted_left = min(spacers[0], left_spacer)
                spacers[0] = 2 if adjusted_left <= 0 else adjusted_left
                spacers[1] = max(spacers[1], spacers_count_)

        pattern = r'^ *< *user[ ._+-]marker[ ._+-](?P<case>one|multi)[ ._+-]?line *>'
        all_lines = text.get_list_of_lines(*lines)

        lst: List[str] = []
        is_continue = False
        baseline_spacers_count = None
        index = 0

        while index < len(all_lines):
            line = all_lines[index]

            # Handle continuation case
            if is_continue:
                spacers_count = len(text.Line.get_leading(line))
                if baseline_spacers_count is None:
                    baseline_spacers_count = spacers_count
                    update_last_column_info(
                        self.last_column_data_info, line,
                        spacers_count, baseline_spacers_count
                    )
                    index += 1
                    continue
                elif spacers_count > 0.8 * baseline_spacers_count:
                    update_last_column_info(
                        self.last_column_data_info, line,
                        spacers_count, baseline_spacers_count
                    )
                    index += 1
                    continue
                else:
                    is_continue = False
                    baseline_spacers_count = None

            # Handle user marker
            match = re.match(pattern, line)
            if match:
                is_oneline = match.group('case').lower() == 'one'
                if is_oneline:
                    first_col_data = re.sub(pattern, '', line)
                    next_line = re.sub(pattern, '',
                                       all_lines[index + NUMBER.ONE])
                    leading = text.Line.get_leading(next_line)

                    self.first_column_data_info[len(lst)] = first_col_data
                    self.first_column_data_info['spacers_count'] = len(leading)
                    indices = self.first_column_data_info.setdefault('indices',
                                                                     [])
                    indices.append(next_line)

                    lst.append(next_line)
                    index += 1
                else:
                    indices = self.last_column_data_info.setdefault('indices',
                                                                    [])
                    new_line = re.sub(pattern, '', line)
                    indices.append(new_line)
                    lst.append(new_line)
                    is_continue = True
            else:
                lst.append(line)

            index += 1

        return lst

    # -------------------------------
    # Column construction
    # -------------------------------

    def add_data_to_rows(self) -> None:
        """Populate rows from lines and attach first column data if available."""
        self.rows.clear()
        for index, line in enumerate(self.lines):
            row = TabularRow(line, ref_row=self.ref_row)
            if index in self.first_column_data_info:
                first_cell = row.cells[0]
                first_cell.set_data(self.first_column_data_info.get(index))
            self.rows.append(row)

    def add_data_to_columns(self) -> None:
        """
        Populate columns from rows and analyze alignment.

        Each row’s cells are distributed into columns. Columns are linked
        left-to-right, and alignment analysis is performed. Extra metadata
        for the last column is also added.
        """
        self.columns.clear()
        is_created = False

        for row in self.rows:
            prev_column = None
            for index, cell in enumerate(row.cells):
                new_col = TabularColumn(index=index)
                column = self.columns[index] if is_created else new_col
                if not is_created:
                    self.columns.append(column)

                column.left_column = prev_column
                column.append_cell(cell)

                if prev_column:
                    prev_column.right_column = column
                prev_column = column
            is_created = True

        for col in self.columns:
            col.analyze_and_update_alignment()

        if self.columns:
            last_column = self.columns[-INDEX.ONE]
            last_column.add_extra_data(self.last_column_data_info.get('lst_data'))

    # -------------------------------
    # Conversion utilities
    # -------------------------------

    def to_list_of_dict(self) -> List[Dict[str, str]]:
        """
        Convert table rows into a list of dictionaries.

        Each row becomes a dictionary mapping column names to cell values.
        Symbol-only rows are skipped.

        Returns
        -------
        list[dict[str, str]]
            List of row dictionaries.
        """
        lst_of_dict: List[Dict[str, str]] = []
        divider = self.divider

        for row_index, row in enumerate(self.rows):
            if row.is_group_of_symbols:
                continue

            dict_obj: Dict[str, str] = {}
            for col in self.columns:
                txt = col.cells[row_index].data.strip()
                txt = txt.strip(divider).strip() if divider else txt
                dict_obj[col.name] = txt
            lst_of_dict.append(dict_obj)

        return lst_of_dict

    # -------------------------------
    # Header cleaning and building
    # -------------------------------

    def do_cleaning_data(self) -> None:
        """
        Clean table data by separating header rows from data rows.

        If a reference row exists and headers are enabled, rows above
        the reference line are treated as headers. Header columns are
        populated accordingly.
        """
        if not self.ref_row:
            return

        if self.is_headers_row:
            ref_line = self.ref_row.line
            if ref_line in self.lines:
                row_pos = self.lines.index(ref_line)
                self.rows = self.rows[row_pos + NUMBER.ONE:]
                self.header_lines = self.lines[:row_pos + NUMBER.ONE]

                for col in self.columns:
                    hdr_col = TabularColumn()
                    hdr_col.cells = col.cells[:row_pos + NUMBER.ONE]
                    self.header_columns.append(hdr_col)
                    col.cells = col.cells[row_pos + NUMBER.ONE:]

    def build_and_update_headers(self) -> None:
        """
        Build and update column headers.

        If headers are enabled and no names are provided, generate names
        from header cells by normalizing text. Otherwise, apply provided
        header names if they match the column count.
        """
        if self.is_headers_row:
            if not self.header_names:
                repl_char = STRING.UNDERSCORE_CHAR
                pat = r'[0-9 \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+'

                for index, hdr_col in enumerate(self.header_columns):
                    col_name = repl_char.join([cell.text for cell in hdr_col.cells])
                    col_name = re.sub(pat, repl_char, col_name)
                    col_name = col_name.strip(repl_char).lower()
                    col_name = col_name or f'col{index}'

                    if col_name in self.header_names:
                        col_name = f'{col_name}{index}'

                    self.header_names.append(col_name)
                    self.columns[index].name = col_name
        else:
            if self.header_names and len(self.header_names) == self.columns_count:
                for index, col_name in enumerate(self.header_names):
                    self.columns[index].name = col_name

    # -------------------------------
    # Processing pipeline
    # -------------------------------

    def process(self) -> None:
        """
        Execute the full parsing pipeline.

        Steps:
        1. Populate rows.
        2. Populate columns.
        3. Clean header data.
        4. Build and update headers.
        """
        self.add_data_to_rows()
        self.add_data_to_columns()
        self.do_cleaning_data()
        self.build_and_update_headers()

    # -------------------------------
    # Regex and template generation
    # -------------------------------

    def to_regex(self) -> str:
        """
        Generate a regex pattern representing the table structure.

        Returns
        -------
        str
            Regex pattern string.
        """
        if not self:
            return STRING.EMPTY

        lst: List[str] = []
        does_prev_col_has_empty_cell = False
        divider_pat = f' *{re.escape(self.divider)} *'
        divider_leading_pat = f'{re.escape(self.divider)} *'
        divider_trailing_pat = f' *{re.escape(self.divider)}'

        for column in self.columns:
            has_empty_cell = does_prev_col_has_empty_cell or column.has_empty_cell
            if self.is_divider:
                if lst:
                    lst.append(divider_pat)
            else:
                sep_pat = PATTERN.SPACE if has_empty_cell else PATTERN.SPACES
                if lst:
                    lst.append(sep_pat)

            lst.append(column.to_regex())
            does_prev_col_has_empty_cell = column.has_empty_cell

        if self.is_start_with_divider:
            lst.insert(NUMBER.ZERO, divider_leading_pat)
        if self.is_leading:
            lst.insert(NUMBER.ZERO, PATTERN.ZOSPACES)
        if self.is_end_with_divider:
            lst.append(divider_trailing_pat)
        if self._is_trailing:
            lst.append(PATTERN.ZOSPACES)

        return text.join_string(*lst)

    def get_header_lines_snippet(self) -> str:
        """
        Extract header lines snippet.

        Returns
        -------
        str
            Concatenated header lines snippet.
        """
        headers_lines = self.raw_headers_data or self.header_lines
        lst: List[str] = []

        for line in text.get_list_of_lines(*headers_lines):
            is_line_of_symbols = bool(re.match(PATTERN.CHECK_PUNCTS_GROUP, line))
            is_header_line = text.Line.has_data(line) and not is_line_of_symbols
            if is_header_line:
                lst.append(line)

        return text.join_string(*lst, separator=STRING.NEWLINE)

    def to_template_snippet(self) -> str:
        """
        Generate a template snippet representing the table.

        Returns
        -------
        str
            Template snippet string.
        """
        if not self:
            return STRING.EMPTY

        lst_of_snippet: List[str] = []
        headers_snippet = self.get_header_lines_snippet()
        if self.is_headers_row and headers_snippet:
            lst_of_snippet.append(headers_snippet)

        self.build_snippet_for_last_column_case(lst_of_snippet)
        self.build_snippet_for_first_column_case(lst_of_snippet)
        self.build_snippet_for_other_case(lst_of_snippet)

        return text.join_string(*lst_of_snippet, separator=STRING.NEWLINE)

    def build_snippet_for_first_column_case(self, lst_of_snippet: List[str]) -> None:
        """
        Build template snippets for the case where the first column
        contains special metadata or indices.

        Parameters
        ----------
        lst_of_snippet : list[str]
            List to append generated snippet strings.

        Notes
        -----
        - Uses `first_column_data_info` to identify layouts.
        - Generates leading/trailing markers and space repetitions.
        - Ensures divider handling is consistent.
        """
        if not self.first_column_data_info:
            return

        leading_snippet = 'start(space)' if self.is_leading else 'start()'
        trailing_snippet = 'end(space) -> record' if self.is_trailing else 'end() -> record'

        first_snippet = self.first_column.to_template_snippet(skipped_empty=True)
        first_snippet = f'{leading_snippet} {first_snippet} end(space) -> Next'

        indices = self.first_column_data_info.get('indices', [])
        layouts = [row.row_layout for row in self.rows if row.line in indices]

        for layout in sorted(set(layouts), reverse=True):
            parts = []
            for index, bit in enumerate(layout):
                column = self.columns[index]
                m, n = column.width, column.max_width
                if m == n:
                    m = n - 4 if (n - 4) > 2 else abs(n - 2)
                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = {}
                if self.last_column_data_info and index == self.columns_count - NUMBER.ONE:
                    kwargs.update(added_list_meta_data=True)

                col_snippet = column.to_template_snippet(**kwargs)
                parts.append(col_snippet if int(bit) else space_snippet)

            sep = self.divider_snippet if self.is_divider else STRING.DOUBLE_SPACES
            next_snippet = text.join_string(*parts, separator=sep)

            if self.is_divider:
                next_snippet = f'{self.divider_leading_snippet}{next_snippet}{self.divider_trailing_snippet}'
                next_snippet = f'start() {next_snippet} {trailing_snippet}'
            else:
                if re.search(r' +space[(]repetition_\d+_\d+[)] *$', next_snippet):
                    next_snippet = re.sub(r' +space[(]repetition_\d+_\d+[)] *$', ' end(space)', next_snippet)
                else:
                    next_snippet = f'{next_snippet} {trailing_snippet}'

                if re.match(r' *space[(]repetition_\d+_\d+[)] *', next_snippet):
                    next_snippet = f'start() {next_snippet}'
                else:
                    next_snippet = f'{leading_snippet} {next_snippet}'

            next_snippet = re.sub(r' +(space[(]repetition_\d+_\d+[)]) +', r' \1 ', next_snippet)

            lst_of_snippet.append(first_snippet)
            lst_of_snippet.append(next_snippet)

    def build_snippet_for_last_column_case(self, lst_of_snippet):
        if not self.last_column_data_info:
            return

        leading_snippet = 'start(space)' if self.is_leading else 'start()'

        first_snippet = self.first_column.to_template_snippet(to_bared_snippet=True)
        if self.is_divider:
            first_snippet = f'{self.divider_leading_snippet}{first_snippet}'
        lst_of_snippet.append(f'{leading_snippet} {first_snippet}zero_or_spaces() -> continue.record')

        indices = self.last_column_data_info.get('indices', [])
        layouts = []
        for row in self.rows:
            if row.line in indices:
                row.row_layout not in layouts and layouts.append(row.row_layout)

        for layout in sorted(layouts, reverse=True):
            lst = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width
                if m == n:
                    m = n - 4 if (n - 4) > 2 else abs(n - 2)
                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = dict()
                if index == self.columns_count - NUMBER.ONE:
                    kwargs.update(added_list_meta_data=True)
                col_snippet = column.to_template_snippet(**kwargs)

                if int(bit) or self.is_divider:
                    lst.append(col_snippet if int(bit) else space_snippet)
                else:
                    if lst:
                        last_item = lst[-INDEX.ONE]
                        pat = r'space[(]repetition_(?P<m>\d+)_(?P<n>\d+)[)]$'
                        match = re.match(pat, last_item)
                        if match:
                            m, n = int(match.group('m')), int(match.group('n'))
                            m += column.width
                            n += column.max_width - column.max_edge_leading_width
                            if m == n:
                                m = n - 4 if (n - 4) > 2 else abs(n - 2)
                            extend_space_snippet = f'space(repetition_{m}_{n})'
                            if lst:
                                lst.pop()
                            lst.append(extend_space_snippet)
                        else:
                            lst.append(space_snippet)
                    else:
                        lst.append(space_snippet)

            sep = self.divider_snippet if self.is_divider else STRING.DOUBLE_SPACES
            line_snippet = text.join_string(*lst, separator=sep)
            if self.is_divider:
                line_snippet = f'{self.divider_leading_snippet}{line_snippet}{self.divider_trailing_snippet}'

            pat = r' *space[(]repetition_\d+_\d+[)] *$'
            if re.search(pat, line_snippet):
                line_snippet = re.sub(pat, ' end(space) -> continue', line_snippet)
            else:
                line_snippet = f'{line_snippet} end(space) -> continue'

            pat = r' *space[(]repetition_\d+_\d+[)] *'
            if re.match(pat, line_snippet):
                line_snippet = f'start() {line_snippet}'
            else:
                line_snippet = f'{leading_snippet} {line_snippet}'

            pat = r' +(space[(]repetition_\d+_\d+[)]) +'
            line_snippet = re.sub(pat, r' \1 ', line_snippet)
            lst_of_snippet.append(line_snippet)

        last_snippet = self.last_column.to_template_snippet(skipped_empty=True, added_list_meta_data=True)
        m, n = self.last_column_data_info.get('spacers')
        m = n - 4 if (n - 4) > 0 else m
        spacer_snippet = f'start() space(repetition_{m}_{n+2}) {last_snippet} end(space) -> continue'
        lst_of_snippet.append(spacer_snippet)

    def build_snippet_for_other_case(self, lst_of_snippet: List[str]) -> None:
        """
        Build template snippets for rows that are neither first-column
        nor last-column special cases.

        Parameters
        ----------
        lst_of_snippet : list[str]
            List to append generated snippet strings.

        Notes
        -----
        - Excludes rows identified in first/last column indices.
        - Ensures uniqueness of generated snippets.
        """
        leading_snippet = 'start(space)' if self.is_leading else 'start()'
        trailing_snippet = 'end(space) -> record' if self.is_trailing else 'end() -> record'

        a_indices = self.first_column_data_info.get('indices', [])
        b_indices = self.last_column_data_info.get('indices', [])
        layouts = [
            row.row_layout
            for row in self.rows
            if row.line not in a_indices and row.line not in b_indices
        ]

        for layout in sorted(layouts, reverse=True):
            parts = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width
                m = n - 2 if m == n and m > 1 else m
                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = dict()
                if self.last_column_data_info and index == self.columns_count - NUMBER.ONE:
                    kwargs.update(added_list_meta_data=True)
                col_snippet = column.to_template_snippet(**kwargs)

                if int(bit) or self.is_divider:
                    parts.append(col_snippet if int(bit) else space_snippet)
                else:
                    if parts:
                        last_item = parts[-INDEX.ONE]
                        pat = r'space[(]repetition_(?P<m>\d+)_(?P<n>\d+)[)]$'
                        match = re.match(pat, last_item)
                        if match:
                            m, n = int(match.group('m')), int(match.group('n'))
                            m += column.width
                            n += column.max_width - column.max_edge_leading_width
                            extend_space_snippet = f'space(repetition_{m}_{n})'
                            parts.pop()
                            parts.append(extend_space_snippet)
                        else:
                            parts.append(space_snippet)
                    else:
                        parts.append(space_snippet)

            sep = self.divider_snippet if self.is_divider else STRING.DOUBLE_SPACES
            line_snippet = text.join_string(*parts, separator=sep)
            if self.is_divider:
                line_snippet = f'{self.divider_leading_snippet}{line_snippet}{self.divider_trailing_snippet}'

            space_end_pat = r' *space[(]repetition_\d+_\d+[)] *$'
            if re.search(space_end_pat, line_snippet):
                line_snippet = re.sub(space_end_pat, ' end(space) -> record', line_snippet)
            else:
                line_snippet = f'{line_snippet} {trailing_snippet}'

            space_any_pat = r' *space[(]repetition_\d+_\d+[)] *'
            if re.match(space_any_pat, line_snippet):
                line_snippet = f'start() {line_snippet}'
            else:
                line_snippet = f'{leading_snippet} {line_snippet}'

            space_between_pat = r' +(space[(]repetition_\d+_\d+[)]) +'
            line_snippet = re.sub(space_between_pat, r' \1 ', line_snippet)

            # Ensure uniqueness
            is_line_snippet_existed = False
            pattern = r'(?i) *start\(\w*\) *(?P<chk>.+) *end\(\w*\) -> (record|continue)'
            match = re.match(pattern, line_snippet)
            if match:
                baseline_chk = match.group('chk')
                for snippet_ in lst_of_snippet:
                    if is_line_snippet_existed:
                        break
                    other_match = re.match(pattern, snippet_)
                    if other_match:
                        is_line_snippet_existed = other_match.group('chk') == baseline_chk
            if not is_line_snippet_existed:
                lst_of_snippet.append(line_snippet)


class TabularCell(RuntimeException):
    """
    Represents a single cell in a tabular text row.

    A `TabularCell` manages its text content, positional boundaries,
    whitespace handling, and alignment relative to reference cells.
    It provides utilities for analyzing leading/trailing spaces,
    computing width, and adjusting positions during parsing.

    Parameters
    ----------
    line : str
        The raw text line containing the cell.
    left_pos : int
        Left boundary index of the cell within the line.
    right_pos : int
        Right boundary index of the cell within the line.
    ref_cell : TabularCell, optional
        Reference cell used for alignment and adjustments.

    Attributes
    ----------
    line : str
        The raw text line.
    data : str
        Substring representing the cell content.
    left : int
        Left boundary index.
    right : int
        Right boundary index.
    inner_left : int
        Left boundary excluding leading spaces.
    inner_right : int
        Right boundary excluding trailing spaces.
    ref_cell : TabularCell or None
        Reference cell for alignment.
    _leading : str or None
        Cached leading spaces.
    _trailing : str or None
        Cached trailing spaces.

    Notes
    -----
    - Provides utilities to detect empty cells, whitespace patterns,
      and groups of characters.
    - Supports positional adjustments relative to neighboring cells.
    """

    def __init__(self, line: str, left_pos: int, right_pos: int, ref_cell: "TabularCell" = None):
        self.args = (line, left_pos, right_pos, ref_cell)

        self._leading = None
        self._trailing = None

        self.left = NUMBER.ZERO
        self.right = NUMBER.ZERO
        self.inner_left = NUMBER.ZERO
        self.inner_right = NUMBER.ZERO

        self.line = STRING.EMPTY
        self.data = STRING.EMPTY

        self.ref_cell = None

        self.process()

    def __len__(self) -> int:
        """Return 1 if the cell has valid boundaries, otherwise 0."""
        return int(self.left >= NUMBER.ZERO) or (self.right > self.left)

    def __repr__(self) -> str:
        """Return a string representation with text, data, and boundaries."""
        cls_name = Misc.get_instance_class_name(self)
        return f"{cls_name}(text={self.text!r}, data={self.data!r}, left={self.left}, right={self.right})"

    # -----------------------------
    # Content and whitespace analysis
    # -----------------------------

    @property
    def text(self) -> str:
        """Return the trimmed text content of the cell."""
        return self.data.strip()

    @property
    def leading(self) -> str:
        """Return leading spaces of the cell content."""
        if self._leading is None:
            self._leading = text.Line.get_leading(self.data)
        return self._leading or STRING.EMPTY

    @property
    def trailing(self) -> str:
        """Return trailing spaces of the cell content."""
        if self._trailing is None:
            if self.is_empty:
                self._trailing = STRING.EMPTY
            else:
                matches = re.findall(PATTERN.SPACESATEOS, self.data)
                self._trailing = matches[NUMBER.ZERO] if matches else STRING.EMPTY
        return self._trailing or STRING.EMPTY

    @property
    def is_empty(self) -> bool:
        """Return True if the cell contains no text."""
        return self.text == STRING.EMPTY

    @property
    def items_count(self) -> int:
        """Return the number of items (words) in the cell."""
        return NUMBER.ZERO if self.is_empty else len(re.split(PATTERN.SPACES, self.text))

    @property
    def width(self) -> int:
        """Return the effective width of the cell."""
        base_width = self.right - self.left
        actual_width = len(self.data)
        return actual_width if base_width <= 0 else min(actual_width, base_width)

    # -----------------------------
    # Whitespace classification
    # -----------------------------

    @property
    def is_leading(self) -> bool: return self.leading != STRING.EMPTY
    @property
    def is_single_leading(self) -> bool: return self.leading == STRING.SPACE_CHAR
    @property
    def is_multi_leading(self) -> bool: return len(self.leading) > NUMBER.ONE

    @property
    def is_trailing(self) -> bool: return self.trailing != STRING.EMPTY
    @property
    def is_single_trailing(self) -> bool: return self.trailing == STRING.SPACE_CHAR
    @property
    def is_multi_trailing(self) -> bool: return len(self.trailing) > NUMBER.ONE

    @property
    def is_just_chars(self) -> bool:
        """Return True if the cell contains only characters without spaces."""
        return not self.is_empty and STRING.SPACE_CHAR not in self.text

    @property
    def is_group_of_chars(self) -> bool:
        """Return True if the cell contains multiple characters separated by spaces."""
        return not self.is_empty and STRING.SPACE_CHAR in self.text

    @property
    def is_containing_space(self) -> bool: return STRING.SPACE_CHAR in self.text
    @property
    def is_not_containing_space(self) -> bool: return STRING.SPACE_CHAR not in self.text
    @property
    def is_containing_spaces(self) -> bool: return STRING.DOUBLE_SPACES in self.text

    # -----------------------------
    # Position and adjustment
    # -----------------------------

    def update_position(self, attr: str, val: int = 0) -> None:
        """Update left or right boundary and reprocess the cell."""
        attr = "left" if attr.lower() == "left" else "right"
        setattr(self, attr, val)
        self.process()

    def get_possible_prefix(self) -> str:
        """Return possible prefix before the last space in the text."""
        if self.is_empty or self.is_trailing:
            return STRING.EMPTY
        *chk, prefix = self.text.rsplit(STRING.SPACE_CHAR, maxsplit=NUMBER.ONE)
        return STRING.EMPTY if chk else prefix

    def get_postfix_data(self) -> str:
        """Return postfix data after the last space or double space."""
        if self.is_multi_trailing or not self.is_containing_space:
            return STRING.EMPTY

        repl = STRING.DOUBLE_SPACES if self.is_containing_spaces else STRING.SPACE_CHAR
        _, remaining_txt = str.rsplit(self.text, repl, maxsplit=NUMBER.ONE)
        ret_val = f"{remaining_txt}{self.trailing}"

        if self.ref_cell:
            other_right = self.right - len(ret_val)
            if other_right > self.ref_cell.inner_right:
                return ret_val
            elif STRING.SPACE_CHAR in remaining_txt:
                _, remaining_txt1 = str.rsplit(remaining_txt, STRING.SPACE_CHAR, maxsplit=NUMBER.ONE)
                return f"{remaining_txt1}{self.trailing}"
            return STRING.EMPTY
        return ret_val

    def do_first_pass_adjustment(self, prev_cell: "TabularCell" = None) -> None:
        """Adjust boundaries based on possible prefix of the previous cell."""
        if not isinstance(prev_cell, self.__class__):
            return

        prefix = prev_cell.get_possible_prefix()
        if prefix and not self.is_leading:
            shift = len(prefix)
            self.left -= shift
            prev_cell.right -= shift
            self.process()
            prev_cell.process()

    def readjust(self, prev_cell: "TabularCell" = None) -> None:
        """Readjust boundaries based on postfix data of the previous cell."""
        if not isinstance(prev_cell, self.__class__):
            # skip adjustment
            return

        if prev_cell.is_multi_trailing or prev_cell.is_empty or (
            prev_cell.is_single_trailing and self.is_leading
        ):
            # skip adjustment
            return

        prefix = prev_cell.get_postfix_data()
        if prefix:
            width = len(prefix) + NUMBER.ONE
            self.update_position("left", val=self.left - width)
            prev_cell.update_position("right", val=self.right - width)

    def process(self) -> None:
        """Validate positions and initialize cell data."""
        line, left_pos, right_pos, ref_cell = self.args

        is_left, left = number.try_to_get_number(left_pos, return_type=int)
        is_right, right = number.try_to_get_number(right_pos, return_type=int)

        if not is_left:
            self.raise_runtime_error(
                msg=(
                    f"Invalid left position in {self.__class__.__name__}.\n"
                    f"Expected: integer value\n"
                    f"Received: {left_pos!r}"
                )
            )
        if not is_right:
            self.raise_runtime_error(
                msg=(
                    f"Invalid right position in {self.__class__.__name__}.\n"
                    f"Expected: integer value\n"
                    f"Received: {right_pos!r}"
                )
            )

        self._leading = None
        self._trailing = None

        if isinstance(ref_cell, self.__class__) or ref_cell is None:
            self.ref_cell = ref_cell
        else:
            cls_name = Misc.get_instance_class_name(self)
            self.raise_runtime_error(
                msg=(
                    f"Invalid ref_cell type detected in {cls_name}.\n"
                    f"Object: {self!r}\n"
                    "Hint: Ensure the reference cell is initialized with a supported type."
                )
            )

        self.left = left
        self.right = len(line) if self.ref_cell and right == 999999 else right
        self.line = line
        self.data = self.line[self.left:self.right]

        self.inner_left = self.left + len(self.leading)
        self.inner_right = self.right - len(self.trailing)

    def set_data(self, data: str) -> None:
        """
        Update the cell's content and reset cached whitespace metadata.

        This method replaces the current `data` string with the provided value
        and clears cached leading/trailing whitespace information so that they
        will be recomputed on the next access.

        Parameters
        ----------
        data : str
            The new text content to assign to the cell.
        """
        self.data = data
        self._leading = None
        self._trailing = None


class TabularRow(RuntimeException):
    """
    Represents a row in a tabular text structure.

    A `TabularRow` manages its cells, alignment, and layout, and can be
    constructed from reference rows or parsing strategies such as regex
    findall, splitting, or variable matching.

    Parameters
    ----------
    line : str
        The raw text line representing the row.
    ref_row : TabularRow, optional
        A reference row used to align and adjust cells.
    aligned : bool, optional
        Whether the row should be aligned with its reference row. Default is True.

    Attributes
    ----------
    line : str
        The raw text line.
    ref_row : TabularRow or None
        Reference row for alignment.
    aligned : bool
        Whether alignment is applied.
    cells : list[TabularCell]
        List of cells parsed from the row.
    row_layout : str
        Binary string representing presence/absence of text in each cell.
    _is_symbols_group : bool or None
        Cached flag indicating whether the row is composed of only symbols.

    Notes
    -----
    - Rows can be created using regex findall, splitting by a separator,
      or variable group matching.
    - Provides utilities to append new cells and analyze row layout.
    """

    def __init__(self, line: str, ref_row: "TabularRow" = None, aligned: bool = True):
        self._is_symbols_group = None
        self.aligned = aligned
        self.line = line
        self.ref_row = ref_row
        self.row_layout = ""
        self.cells = []
        self.process()

    def __len__(self) -> int:
        """Return 1 if the row has cells, otherwise 0."""
        return int(bool(self.cells))

    def __repr__(self) -> str:
        """Return a string representation with the number of columns."""
        cls_name = Misc.get_instance_class_name(self)
        return f"{cls_name}(columns_count={len(self.cells)})"

    @property
    def cells_count(self) -> int:
        """Number of cells in the row."""
        return len(self.cells)

    @property
    def columns_count(self) -> int:
        """Alias for `cells_count`."""
        return self.cells_count

    @property
    def is_group_of_symbols(self) -> bool:
        """Return True if the row consists only of symbols."""
        if self._is_symbols_group is None:
            if not self.cells:
                return False
            # pattern = ' *%(p)s( +%(p)s)* *$' % dict(p=PATTERN.PUNCTS)
            pattern = rf" *{PATTERN.PUNCTS}( +{PATTERN.PUNCTS})* *$"
            self._is_symbols_group = bool(re.match(pattern, self.line))
        return self._is_symbols_group

    def append_new_cell(self, left_pos: int, right_pos: int) -> "TabularCell":
        """Append a new cell to the row based on positions and reference row."""
        index = len(self.cells)
        ref_cell = self.ref_row.cells[index] if self.ref_row else None
        cell = TabularCell(self.line, left_pos, right_pos, ref_cell=ref_cell)

        if self.ref_row:
            prev_cell = self.cells[-NUMBER.ONE] if index else None
            if self.ref_row.aligned:
                cell.do_first_pass_adjustment(prev_cell=prev_cell)

        self.cells.append(cell)
        return cell

    def process(self) -> None:
        """Initialize cells based on the reference row."""
        self.cells.clear()
        if self.ref_row:
            for ref_cell in self.ref_row.cells:
                cell = self.append_new_cell(ref_cell.left, ref_cell.right)
                bit = 1 if cell.text else 0
                self.row_layout += str(bit)

    # -----------------------------
    # Reference row creation methods
    # -----------------------------

    @classmethod
    def do_creating_ref_row(cls, line: str, pattern: str, tokens: list[str], aligned: bool = True) -> "TabularRow":
        """Create a reference row from parsed tokens."""
        if not tokens:
            RuntimeException.do_raise_runtime_error(
                obj=f"{cls.__name__}RTError",
                msg=(
                    f"Parsing failed for {cls.__name__}.\n"
                    f"Pattern: {pattern!r}\n"
                    f"Line: {line!r}\n"
                    "Reason: no valid tokens were extracted."
                ),
            )

        ref_row = cls(line, aligned=aligned)
        prev_right, cell = 0, None

        for item in tokens:
            left = prev_right
            prev_right = line.index(item) if cell is None else prev_right
            right = prev_right + len(item)
            prev_right = right
            cell = ref_row.append_new_cell(left, right)
        else:
            if cell:
                cell.right = 999999

        return ref_row

    @classmethod
    def do_creating_ref_row_by_findall(cls, line: str, pattern: str, columns_count: int = -1) -> "TabularRow":
        """Create a reference row using regex findall."""
        tokens = re.findall(pattern, line)
        total = len(tokens)

        if columns_count > 0 and columns_count != total:
            RuntimeException.do_raise_runtime_error(
                obj=f"{cls.__name__}RTError",
                msg=(
                    f"Column count mismatch in {cls.__name__}.\n"
                    f"Parsed columns: {total} | Expected columns: {columns_count}\n"
                    f"Pattern: {pattern!r}\n"
                    f"Line: {line!r}\n"
                    "Hint: Verify the input line matches the expected pattern structure."
                ),
            )

        return cls.do_creating_ref_row(line, pattern, tokens)

    @classmethod
    def do_creating_ref_row_by_splitting(cls, line: str, separator: str, columns_count: int = 1) -> "TabularRow":
        """Create a reference row by splitting the line using a separator."""
        pattern = re.escape(separator)
        tokens = re.split(pattern, line)
        total = len(tokens)

        # Handle edge cases with prefix/postfix separators
        if total == columns_count + NUMBER.TWO:
            prefix, first = tokens.pop(NUMBER.ZERO), tokens.pop(NUMBER.ZERO)
            tokens.insert(NUMBER.ZERO, text.join_string(prefix, first, separator=separator))

            postfix, last = tokens.pop(), tokens.pop()
            tokens.append(text.join_string(last, postfix, separator=separator))
            total = len(tokens)

        elif total == columns_count + NUMBER.ONE:
            if line.strip().startswith(separator):
                prefix, first = tokens.pop(NUMBER.ZERO), tokens.pop(NUMBER.ZERO)
                tokens.insert(NUMBER.ZERO, text.join_string(prefix, first, separator=separator))
            elif line.strip().endswith(separator):
                postfix, last = tokens.pop(), tokens.pop()
                tokens.append(text.join_string(last, postfix, separator=separator))
            total = len(tokens)

        if columns_count > 0 and columns_count != total:
            RuntimeException.do_raise_runtime_error(
                obj=f"{cls.__name__}RTError",
                msg=(
                    f"Column count mismatch in {cls.__name__}.\n"
                    f"Parsed columns: {total}\n"
                    f"Expected columns: {columns_count}\n"
                    f"Pattern: {pattern!r}\n"
                    f"Line: {line!r}\n"
                    "Hint: Ensure the input line matches the expected pattern structure."
                ),
            )

        return cls.do_creating_ref_row(line, pattern, tokens, aligned=False)

    @classmethod
    def do_creating_ref_row_by_variable(cls, line: str, pattern: str) -> "TabularRow":
        """Create a reference row using regex named groups (v000, v001, ...)."""
        match = re.match(pattern, line)
        result = match.groupdict() if match else {}
        tokens = [result.get(f"v{i:03d}") for i in range(256) if f"v{i:03d}" in result]

        return cls.do_creating_ref_row(line, pattern, tokens)

    @classmethod
    def create_ref_row(cls, line: str, pattern: str, case: str = "", columns_count: int = -1) -> "TabularRow":
        """
        Factory method to create a reference row using different parsing strategies.

        Parameters
        ----------
        line : str
            Input line to parse.
        pattern : str
            Regex pattern or separator string.
        case : str, optional
            Parsing strategy: "findall", "variable", or "split".
        columns_count : int, optional
            Expected number of columns. Default is -1 (no check).

        Returns
        -------
        TabularRow
            A reference row created using the specified strategy.

        Raises
        ------
        RuntimeError
            If the parsing strategy is unsupported or column count mismatches.
        """

        if case == "findall":
            return cls.do_creating_ref_row_by_findall(line, pattern, columns_count)
        elif case == "variable":
            return cls.do_creating_ref_row_by_variable(line, pattern)
        elif case == "split":
            return cls.do_creating_ref_row_by_splitting(line, pattern, columns_count)
        else:
            return RuntimeException.do_raise_runtime_error(
                obj=f"{cls.__name__}RTError",
                msg=(
                    f"Unsupported case encountered in create_ref_row.\n"
                    f"Case value: {case!r}\n"
                    f"Class: {cls.__name__}\n"
                    "Hint: Verify that the provided case is valid and supported."
                ),
            )


class TabularColumn:
    """
    Represents a single column in a tabular text structure.

    A `TabularColumn` holds metadata about its position, alignment, and
    associated cells. It can generate regex patterns and template snippets
    for parsing tabular text.

    Parameters
    ----------
    index : int, optional
        Column index (default is 0).
    name : str, optional
        Column name. Defaults to "col{index}" if not provided.
    left_column : TabularColumn, optional
        Reference to the column on the left.
    right_column : TabularColumn, optional
        Reference to the column on the right.
    is_last : bool, optional
        Whether this column is the last in the table. Default is False.

    Attributes
    ----------
    cells : list
        List of cell objects belonging to this column.
    extra_data : list or None
        Additional metadata or text fragments associated with the column.
    left_border : int
        Left boundary position of the column.
    right_border : int
        Right boundary position of the column.
    _alignment : str
        Alignment of the column ("left", "right", or "center").

    Notes
    -----
    - Alignment is inferred based on cell positions.
    - Regex and template snippet generation depend on the cell contents.
    """

    def __init__(self, index=0, name="", left_column=None, right_column=None, is_last=False):
        self.left_column = left_column
        self.right_column = right_column
        self.is_last = is_last

        self.extra_data = None
        self.index = index
        self.name = name or f"col{index}"
        self.cells = []
        self.left_border = NUMBER.ZERO
        self.right_border = NUMBER.ZERO
        self._alignment = "left"

    def __len__(self) -> int:
        """Return 1 if the column has cells, otherwise 0."""
        return int(bool(self.cells))

    def __repr__(self) -> str:
        """Return a string representation of the column with name and cell count."""
        cls_name = Misc.get_instance_class_name(self)
        return f"{cls_name}(name={self.name!r}, cells_count={len(self.cells)})"

    @property
    def cells_count(self) -> int:
        """Number of cells in the column."""
        return len(self.cells)

    @property
    def rows_count(self) -> int:
        """Alias for `cells_count`."""
        return self.cells_count

    @property
    def is_left_alignment(self) -> bool:
        """Return True if column alignment is left."""
        return bool(self and self._alignment == "left")

    @property
    def is_right_alignment(self) -> bool:
        """Return True if column alignment is right."""
        return bool(self and self._alignment == "right")

    @property
    def is_center_alignment(self) -> bool:
        """Return True if column alignment is center."""
        return not self.is_left_alignment and not self.is_right_alignment

    @property
    def width(self) -> int:
        """Compute the effective width of the column based on cell widths."""
        widths = [cell.width for cell in self.cells if cell.width]
        if not widths:
            return NUMBER.ZERO

        max_width = max(widths)
        if len(set(widths)) == NUMBER.ONE:
            return max_width

        left_positions = {cell.left for cell in self.cells}
        right_positions = {cell.right for cell in self.cells}

        if len(left_positions) == NUMBER.ONE:
            common_width, _ = Counter(widths).most_common().pop(0)
            return max_width if common_width == max_width else math.ceil(statistics.mean(widths))
        elif len(right_positions) == NUMBER.ONE:
            return max_width
        return math.ceil(statistics.mean(widths))

    @property
    def max_edge_trailing_width(self) -> int:
        """Maximum trailing width contributed by the right column."""
        if not self.right_column:
            return NUMBER.ZERO

        trailing_lengths = [
            len(text.Line.get_leading(cell.data))
            for cell in self.right_column.cells
            if cell.data.strip()
        ]
        if not trailing_lengths:
            return NUMBER.ZERO

        edge_width = max(trailing_lengths)
        return NUMBER.ZERO if self.right_column.width == edge_width else edge_width

    @property
    def max_edge_leading_width(self) -> int:
        """Maximum leading width contributed by the left column."""
        if not self.left_column:
            return NUMBER.ZERO

        leading_lengths = [
            len(text.Line.get_trailing(cell.data))
            for cell in self.left_column.cells
            if cell.data.strip()
        ]
        if not leading_lengths:
            return NUMBER.ZERO

        edge_width = max(leading_lengths)
        return NUMBER.ZERO if self.left_column.width == edge_width else edge_width

    @property
    def max_width(self) -> int:
        """Return the maximum width including leading and trailing edges."""
        return self.width + self.max_edge_trailing_width + self.max_edge_leading_width

    @property
    def has_empty_cell(self) -> bool:
        """Return True if any cell in the column is empty."""
        return any(cell.is_empty for cell in self.cells)

    def add_extra_data(self, extra_data) -> None:
        """Attach extra metadata to the column."""
        self.extra_data = extra_data

    def append_cell(self, cell) -> None:
        """Append a cell to the column."""
        self.cells.append(cell)

    def analyze_and_update_alignment(self) -> None:
        """Analyze cell positions and update column alignment."""
        if not self.cells:
            return

        left_edges = {cell.left + len(cell.leading) for cell in self.cells}
        right_edges = {cell.right + len(cell.trailing) for cell in self.cells}

        key = f"{int(len(left_edges) == NUMBER.ONE)}{int(len(right_edges) == NUMBER.ONE)}"
        alignment_map = {"11": "left", "10": "left", "01": "right", "00": "center"}
        self._alignment = alignment_map.get(key, "left")

    def to_regex(self) -> str:
        """Generate a regex pattern for the column based on its cells."""
        if not self:
            return STRING.EMPTY

        texts = [cell.text for cell in self.cells if cell.text]
        if self.extra_data:
            texts.extend(self.extra_data)

        node = TranslatedPattern.do_factory_create(*texts)
        pattern = node.get_regex_pattern(var=self.name)

        if node.is_group() and not self.is_last:
            max_items = max(cell.items_count for cell in self.cells)
            occurrence = max_items - NUMBER.ONE
            if occurrence > NUMBER.ZERO:
                pattern = f"{pattern[:-NUMBER.TWO]}{{,{occurrence}}})"

        if self.has_empty_cell:
            first, last = str.split(pattern, ">", maxsplit=1)
            pattern = f"{first}>( {{{self.width},{self.max_width}}})|( *{last[:-NUMBER.ONE]} *))"

        return pattern

    def to_template_snippet(
        self,
        added_list_meta_data: bool = False,
        skipped_empty: bool = False,
        to_bared_snippet: bool = False,
    ) -> str:
        """Generate a template snippet for the column."""
        if not self:
            return STRING.EMPTY

        texts = [cell.text for cell in self.cells if cell.text]
        if self.extra_data:
            texts.extend(self.extra_data)

        node = TranslatedPattern.do_factory_create(*texts)
        kwargs = {} if to_bared_snippet else {"var": self.name}
        snippet = node.get_template_snippet(**kwargs)

        if to_bared_snippet or (skipped_empty and not added_list_meta_data):
            return snippet

        if node.is_group() and not self.is_last:
            max_items = max(cell.items_count for cell in self.cells)
            occurrence = max_items - NUMBER.ONE
            if occurrence > NUMBER.ZERO:
                if "_phrase" in snippet or re.match(r"(mixed_)?words", snippet):
                    fmt = "%s, at_most_%s_phrase_occurrences)"
                else:
                    fmt = "%s, at_most_%s_group_occurrences)"
                snippet = node.singular_name + "(" + snippet.split("(", 1)[-1]
                snippet = fmt % (snippet[:-INDEX.ONE], occurrence)

        if added_list_meta_data:
            snippet = f"{snippet[:-INDEX.ONE]}, meta_data_list)"

        return snippet
