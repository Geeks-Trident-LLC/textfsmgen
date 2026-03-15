"""
textfsmgen.engine.tabular
=========================

Provides utilities for parsing tabular text into structured representations
that can be converted into regex patterns or template snippets.
"""

from typing import List, Tuple, Dict, Optional, Any
from collections import Counter
import math
import statistics
import operator as op
import re

from textfsmgen.core.patterns import LinePattern
from textfsmgen.libs import PATTERN
from textfsmgen.libs import datatype
from textfsmgen.libs import text
from textfsmgen.libs import number

from textfsmgen.engine.translate import PatternTranslator
from textfsmgen.exceptions import RuntimeException

from textfsmgen.engine.common import get_line_position_by
from textfsmgen.engine.common import get_fixed_line_snippet


class TabularTranslator(RuntimeException):
    """
    Represents a tabular text pattern that can be parsed into regex patterns
    or template snippets.
    """
    def __init__(
        self, *lines, column_divider='', column_count=0, column_widths=None,
        headers=None, header_rows=None, custom_header_text='',
        starting_from=None, ending_at=None, has_header_row=True
    ):
        self.lines = text.get_list_of_lines(*lines)
        self.kwargs = dict(
            column_divider=column_divider,
            column_count=column_count,
            column_widths=column_widths or [],
            headers=headers,
            header_rows=header_rows,
            custom_header_text=custom_header_text,
            has_header_row=has_header_row
        )

        self.starting_from = starting_from
        self.ending_at = ending_at
        self.tabular_parser = None

        self.index_start = None
        self.index_end = None

        self.prepare_column_widths()
        self.process()

    def __len__(self) -> int:
        """Return 1 if a tabular parser exists, otherwise 0."""
        return int(bool(self.tabular_parser))

    def prepare_column_widths(self) -> None:
        """Validate and normalize column widths."""
        column_widths = self.kwargs.get("column_widths")
        if not column_widths:
            return

        normalized = []
        if text.is_string(column_widths) or datatype.is_list(column_widths):
            if text.is_string(column_widths):
                column_widths = column_widths.strip()
                widths = re.split(r"[ ,]+", column_widths)
            else:
                widths = column_widths[:]

            for idx, width_ in enumerate(widths):
                is_number, width = number.try_to_get_number(width_, return_type=int)
                if is_number:
                    normalized.append(width)
                elif idx == len(widths) - 1:
                    normalized.append("")
                else:
                    self.raise_runtime_error(
                        msg=(
                            f"Invalid column widths in {self.__class__.__name__}.\n"
                            "Expected: list of integers or string of integers\n"
                            f"Received: {column_widths!r}"
                        )
                    )

            self.kwargs.update(column_widths=normalized, column_count=len(normalized))
        else:
            self.raise_runtime_error(
                msg=(
                    f"Invalid column widths in {self.__class__.__name__}.\n"
                    "Expected: list of integers or string of integers\n"
                    f"Received: {column_widths!r}"
                )
            )

    def process(self) -> None:
        """Initialize the tabular parser with the given lines and configuration."""
        self.index_start = get_line_position_by(self.lines, self.starting_from)
        self.index_end = get_line_position_by(self.lines, self.ending_at)

        lines = self.lines[self.index_start:self.index_end]
        self.tabular_parser = VarColumnTabularTranslator(*lines, **self.kwargs)

    def to_regex(self) -> str:
        """Return a regex pattern generated from the parsed table."""
        return self.tabular_parser.to_regex() if self else ""

    def to_template_snippet(self) -> str:
        """Return a template snippet generated from the parsed table."""
        tmpl_snippet = (
            self.tabular_parser.to_template_snippet() if self else ""
        )

        if not tmpl_snippet.strip():
            return tmpl_snippet

        lines = tmpl_snippet.splitlines()
        first_line = lines[0]

        # Handle starting marker
        if self.index_start is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.index_start)
            if line_snippet:
                if re.search(LinePattern(line_snippet), first_line):
                    tmpl_snippet = text.join_string(*lines[1:], separator="\n")
                tmpl_snippet = f"{line_snippet} -> Table\nTable\n{tmpl_snippet}"

        lines = tmpl_snippet.splitlines()
        last_line = lines[-1]

        # Handle ending marker
        if self.index_end is not None:
            line_snippet = get_fixed_line_snippet(self.lines, index=self.index_end)
            if line_snippet:
                if re.search(LinePattern(line_snippet), last_line):
                    tmpl_snippet = text.join_string(*lines[:-1], separator="\n")
                tmpl_snippet = f"{tmpl_snippet}\n{line_snippet} -> EOF"

        return tmpl_snippet


class VarColumnTabularTranslator(RuntimeException):
    """
    Parse tabular text with variable column structures and optional dividers.
    """

    def __init__(
        self, *lines, column_divider='', column_count=0, column_widths=None,
        headers=None, header_rows=None, custom_header_text='',
        has_header_row=True, **kwargs
    ):
        self._is_start_with_divider = None
        self._is_end_with_divider = None

        self.lines = text.get_list_of_lines(*lines)
        self.total_lines = len(self.lines)
        self.column_divider = column_divider
        self.column_widths = column_widths or []
        self.column_count = column_count
        self.ensure_column_count()

        self.header_rows = header_rows
        self.custom_header_text = custom_header_text
        self.raw_header_rows = []
        self.headers = headers
        self.has_header_row = has_header_row
        self.variables = []

        self.kwargs = kwargs
        self.prepare_header_rows()

    def __len__(self):
        """Return True if column_count is non-zero, else False."""
        return bool(self.column_count)

    @property
    def is_punct_divider(self):
        """Check if the column_divider is a punctuation symbol."""
        return bool(re.match(PATTERN.ENDS_WITH_PUNCT, self.column_divider))

    @property
    def is_start_with_divider(self):
        """Check if most lines start with the column_divider symbol."""
        if self._is_start_with_divider is None:
            if self.is_punct_divider:
                count = sum(line.strip().startswith(self.column_divider) for line in self.lines)
                self._is_start_with_divider = op.gt(count, op.truediv(len(self.lines), 2)) if count else False
            else:
                self._is_start_with_divider = False
        return self._is_start_with_divider

    @property
    def is_end_with_divider(self):
        """Check if most lines end with the column_divider symbol."""
        if self._is_end_with_divider is None:
            if self.is_punct_divider:
                count = sum(line.strip().endswith(self.column_divider) for line in self.lines)
                self._is_end_with_divider = op.gt(count, op.truediv(len(self.lines), 2)) if count else False
            else:
                self._is_end_with_divider = False
        return self._is_end_with_divider

    def ensure_column_count(self):
        """Infer column count from lines or raise error if zero."""
        pat = f"{PATTERN.PUNCTS_PHRASE}$"
        for line in self.lines:
            if re.match(pat, line.strip()):
                self.column_count = len(re.split(PATTERN.WSS, line.strip()))
                return
        if not self:
            self.raise_runtime_error(msg='column_count cannot be zero')

    def prepare_header_rows(self):
        """Extract header lines from header_rows (indices or substrings)."""
        lst = self.raw_header_rows
        data = self.header_rows
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

        elif datatype.is_list(data):
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

    def normalize_headers(self):
        """Normalize header names into valid, unique variable identifiers."""
        headers = self.headers
        if not headers:
            return []

        # Accept comma/space‑separated string
        if text.is_string(headers):
            headers = re.split(r"[ ,]+", headers.strip())

        # Only process when header count matches column count
        if not (datatype.is_list(headers) and len(
                headers) == self.column_count):
            return []

        variables = []
        punct_pattern = f"[ {PATTERN.PUNCTS[1:]}]"
        replacement = "_"

        for i, hdr in enumerate(headers):
            cleaned = re.sub(punct_pattern, replacement, hdr.strip())
            cleaned = cleaned if cleaned != replacement else cleaned.rstrip(
                replacement)

            # Ensure uniqueness
            final = f"{cleaned}{i}" if cleaned in variables else cleaned
            variables.append(final)

        return variables

    def default_variables(self):
        """Generate default variable names: col0, col1, ..."""
        return [f"col{i}" for i in range(self.column_count)]

    # -------------------------------
    # Reference row finders
    # -------------------------------

    def find_reference_row_by_divider(self, custom_line=""):
        """Find a reference row defined by repeated punctuation dividers."""
        pattern = r" *%(p)s( +%(p)s){%(n)s} *$" % {
            "p": PATTERN.PUNCTS,
            "n": self.column_count - 1,
        }

        line = custom_line or next(
            (ln for ln in self.lines if re.match(pattern, ln)),
            ""
        )
        if not line:
            return None

        divider_pattern = rf" *{PATTERN.PUNCTS} *"
        return Row.do_creating_reference_row(
            line,
            divider_pattern,
            case="findall",
            column_count=self.column_count,
        )

    def find_reference_row_by_separator(self, custom_line=""):
        """Find a reference row using the explicit column divider."""
        pattern = r" *%(sep)s?(%(cell)s%(sep)s){%(n)s}%(cell)s%(sep)s? *$" % {
            "sep": re.escape(self.column_divider),
            "cell": r"[^%s]+" % self.column_divider,
            "n": self.column_count - 1,
        }

        line = custom_line or next(
            (ln for ln in self.lines if re.match(pattern, ln)),
            ""
        )
        if not line:
            return None

        return Row.do_creating_reference_row(
            line,
            self.column_divider,
            column_count=self.column_count,
            case="split",
        )

    def find_reference_row_by_space_divider(
            self,
            spaces: str = " ",
            custom_line: str = ""
    ) -> Optional["Row"]:
        """Find a reference row where columns are separated by one or more spaces."""
        gap = "" if spaces == " " else " "
        repetition = self.column_count - 1

        # Pattern to detect a valid reference row
        detect_pattern = r" *%(cell)s(%(gap)s +%(cell)s){%(n)s} *$" % {
            "cell": PATTERN.NON_WSS_GROUP,
            "gap": gap,
            "n": repetition,
        }

        line = custom_line or next(
            (ln for ln in self.lines if re.match(detect_pattern, ln)),
            None
        )
        if not line:
            return None

        # Build capturing pattern for variable extraction
        parts = []
        for index in range(self.column_count):
            key = f"v{index:03d}"
            base = {
                "key": key,
                "cell": PATTERN.NON_WSS_GROUP,
                "gap": gap,
            }

            if index == 0:
                fmt = r"(?P<%(key)s> *%(cell)s%(gap)s +)"
            elif index == self.column_count - 1:
                fmt = r"(?P<%(key)s>%(cell)s *)$"
            else:
                fmt = r"(?P<%(key)s>%(cell)s%(gap)s +)"

            parts.append(fmt % base)

        capture_pattern = "".join(parts)

        return Row.do_creating_reference_row(
            line,
            capture_pattern,
            column_count=self.column_count,
            case="variable",
        )

    def find_reference_row_by_single_space(self) -> Optional['Row']:
        """Find reference row using single space column_divider."""
        return self.find_reference_row_by_space_divider()

    def find_reference_row_by_multi_space(self) -> Optional['Row']:
        """Find reference row using multi-space column_divider."""
        return self.find_reference_row_by_space_divider(spaces='  ')

    def find_reference_row_from_custom_header(self) -> Optional['Row']:
        """Find reference row using custom header line."""
        return self.find_reference_row_by_divider(custom_line=self.custom_header_text)

    def find_reference_row_by_column_widths(self, custom_line: str = '') -> Optional[
        'Row']:
        """Find reference row using fixed column widths."""
        parts = [
            f'(?P<v{index:03d}>.{{{width}}})' if index < self.column_count - 1
            else f'(?P<v{index:03d}>.*)'
            for index, width in enumerate(self.column_widths)
        ]
        pattern = text.join_string(*parts)

        line = custom_line or next(
            (ln for ln in self.lines if re.match(pattern, ln)),
            None
        )
        if not line:
            return None

        return Row.do_creating_reference_row(
            line, pattern,
            column_count=self.column_count,
            case='variable'
        )

    # -------------------------------
    # Table parsing
    # -------------------------------

    def try_parse_table_with(self, case: str) -> Tuple[bool, Optional["ParsedTable"]]:
        """Try parsing the table using the given reference-row strategy."""
        strategies = {
            "column_widths": self.find_reference_row_by_column_widths,
            "symbols": self.find_reference_row_by_divider,
            "separator": self.find_reference_row_by_separator,
            "multi_spaces": self.find_reference_row_by_multi_space,
            "blank_space": self.find_reference_row_by_single_space,
            "custom": self.find_reference_row_from_custom_header,
        }

        finder = strategies.get(case, self.find_reference_row_by_single_space)
        ref_row = finder()
        if not ref_row:
            return False, None

        headers = self.normalize_headers()
        table = ParsedTable(
            *self.lines,
            reference_row=ref_row,
            column_divider=self.column_divider,
            headers=headers,
            raw_header_rows=self.raw_header_rows,
            is_start_with_divider=self._is_start_with_divider,
            is_end_with_divider=self._is_end_with_divider,
            has_header_row=self.has_header_row,
        )

        return True, table

    def parse_table(self) -> "ParsedTable":
        """Parse the tabular text using the appropriate divider strategy."""
        strategies = [
            (
                bool(self.column_widths),
                "column_widths",
                "Unable to parse tabular text using fixed column widths.",
            ),
            (
                re.match(f"{PATTERN.PUNCT}$", self.column_divider.strip()),
                "separator",
                f"Unable to parse tabular text using column_divider {self.column_divider!r}.",
            ),
            (
                bool(self.custom_header_text),
                "custom",
                "Unable to parse tabular text using custom header text.",
            ),
            (
                self.column_divider == " ",
                "blank_space",
                "Unable to parse tabular text using a single‑space divider.",
            ),
            (
                re.match(r"  +$", self.column_divider),
                "multi_spaces",
                "Unable to parse tabular text using a multi‑space divider.",
            ),
            (
                self.column_divider == "",
                "symbols",
                "Unable to parse tabular text using an empty/symbol divider.",
            ),
        ]

        case = None
        err_msg = None

        for cond, name, reason in strategies:
            if cond:
                case = name
                err_msg = (
                    f"Parsing failed in {self.__class__.__name__}.\n"
                    f"Case: {case}\n"
                    f"Reason: {reason}"
                )
                break

        if case is None:
            self.raise_runtime_error(
                msg=(
                    f"Unsupported column_divider {self.column_divider!r} in "
                    f"{self.__class__.__name__}.\n"
                    "Hint: Use space, multi‑space, punctuation, or custom header text."
                )
            )

        ok, table = self.try_parse_table_with(case)
        if not ok:
            self.raise_runtime_error(msg=err_msg)

        return table

    def to_regex(self) -> str:
        """Convert parsed tabular text into a regex pattern."""
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
        """Convert parsed tabular text into a template snippet."""
        table = self.parse_table()
        if not table:
            self.raise_runtime_error(
                msg=(
                    f"Unable to build template snippet in {self.__class__.__name__}.\n"
                    "Reason: Provided text is not in a valid tabular format."
                )
            )
        return table.to_template_snippet()


class ParsedTable(RuntimeException):
    """Represents a parsed tabular text structure with rows and columns."""

    def __init__(
        self, *lines: str, reference_row: Optional['Row'] = None,
        column_divider: str = '', column_widths: Optional[List[int]] = None,
        headers: Optional[List[str]] = None,
        raw_header_rows: Optional[List[str]] = None,
        is_start_with_divider: bool = False,
        is_end_with_divider: bool = False,
        has_header_row: bool = True
    ):
        # Column data info
        self.first_column_data_info: Dict[Any, Any] = {}
        self.last_column_data_info: Dict[Any, Any] = {}

        # Raw input
        self.lines: List[str] = self.prepare_lines(lines)
        self.reference_row = reference_row
        self.column_divider: str = column_divider
        self.column_widths: Optional[List[int]] = column_widths

        # Parsed structures
        self.rows: List['Row'] = []
        self.columns: List['Column'] = []
        self.header_lines: List[str] = []
        self.header_columns: List['Column'] = []
        self.headers: List[str] = headers or []
        self.raw_header_rows: List[str] = raw_header_rows or []

        # Internal flags
        self._is_leading: Optional[bool] = None
        self._is_trailing: Optional[bool] = None

        # Divider context
        self.is_start_with_divider: bool = is_start_with_divider
        self.is_end_with_divider: bool = is_end_with_divider
        self.has_header_row: bool = has_header_row

        # Divider snippets for regex/template generation

        self.has_divider: bool = bool(self.column_divider.strip())
        escaped = re.escape(self.column_divider)
        self.divider_snippet: str = f'optional_spaces(){escaped}optional_spaces()'
        self.divider_leading_snippet: str = f'{escaped}optional_spaces()'
        self.divider_trailing_snippet: str = f'optional_spaces(){escaped}'

        self.process()

    def __len__(self) -> int:
        """Return 1 if table has rows and columns, else 0."""
        return int(bool(self.rows) and bool(self.columns))

    def __repr__(self) -> str:
        """Return a string representation of the table."""
        cls_name = datatype.get_class_name(self)
        return f"{cls_name}(rows_count={len(self.rows)}, column_count={len(self.columns)})"

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
    def row_count(self) -> int:
        """Return number of rows."""
        return len(self.rows)

    @property
    def column_count(self) -> int:
        """Return number of columns."""
        return len(self.columns)

    @property
    def first_column(self) -> 'Column':
        """Return the first column."""
        return self.columns[0]

    @property
    def last_column(self) -> 'Column':
        """Return the last column."""
        return self.columns[-1]

    # -------------------------------
    # Line preparation
    # -------------------------------

    def prepare_lines(self, lines: List[str]) -> List[str]:
        """Normalize and preprocess input lines, handling user markers."""

        def update_last_column_info(
                column_info: dict, line_: str, spacers_count_: int, baseline_: int
        ) -> None:
            """Update metadata for the last column with line content
            and spacer information."""
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
            if not match:
                lst.append(line)
                index += 1
                continue

            is_oneline = match.group('case').lower() == 'one'
            if is_oneline:
                first_col_data = re.sub(pattern, '', line)
                next_line = re.sub(pattern, '', all_lines[index + 1])
                leading = text.Line.get_leading(next_line)

                self.first_column_data_info[len(lst)] = first_col_data
                self.first_column_data_info['spacers_count'] = len(leading)
                indices = self.first_column_data_info.setdefault('indices', [])
                indices.append(next_line)

                lst.append(next_line)
                index += 1
            else:
                indices = self.last_column_data_info.setdefault('indices', [])
                new_line = re.sub(pattern, '', line)
                indices.append(new_line)
                lst.append(new_line)
                is_continue = True

            index += 1

        return lst

    # -------------------------------
    # Column construction
    # -------------------------------

    def add_data_to_rows(self) -> None:
        """Populate rows from lines and attach first column data if available."""
        self.rows.clear()
        for index, line in enumerate(self.lines):
            row = Row(line, reference_row=self.reference_row)
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
                new_col = Column(index=index)
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
            last_column = self.columns[-1]
            last_column.add_extra_data(self.last_column_data_info.get('lst_data'))

    # -------------------------------
    # Conversion utilities
    # -------------------------------

    def to_list_of_dict(self) -> List[Dict[str, str]]:
        """Convert table rows into a list of dictionaries."""
        lst_of_dict: List[Dict[str, str]] = []
        divider = self.column_divider

        for row_index, row in enumerate(self.rows):
            if row.is_puncts_group:
                continue

            row_dict: Dict[str, str] = {}
            for col in self.columns:
                txt = col.cells[row_index].data.strip()
                txt = txt.strip(divider).strip() if divider else txt
                row_dict[col.name] = txt
            lst_of_dict.append(row_dict)

        return lst_of_dict

    # -------------------------------
    # Header cleaning and building
    # -------------------------------

    def do_cleaning_data(self) -> None:
        """Clean table data by separating header rows from data rows."""
        if not self.reference_row:
            return

        if not self.has_header_row:
            return

        if not self.reference_row.line in self.lines:
            return

        ref_line = self.reference_row.line
        row_pos = self.lines.index(ref_line)
        self.rows = self.rows[row_pos + 1:]
        self.header_lines = self.lines[:row_pos + 1]

        for col in self.columns:
            hdr_col = Column()
            hdr_col.cells = col.cells[:row_pos + 1]
            self.header_columns.append(hdr_col)
            col.cells = col.cells[row_pos + 1:]

    def build_and_update_headers(self) -> None:
        """Build and update column headers."""
        if self.has_header_row:
            if not self.headers:
                replacement = "_"
                noise_pattern = r'[0-9 \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+'

                for index, hdr_col in enumerate(self.header_columns):
                    # extract column name
                    raw_col_name = replacement.join([cell.text for cell in hdr_col.cells])

                    # normalize: collapse noise -> strip -> lowercase
                    col_name = re.sub(noise_pattern, replacement, raw_col_name)
                    col_name = col_name.strip(replacement).lower() or f'col{index}'

                    # ensure uniqueness
                    if col_name in self.headers:
                        col_name = f'{col_name}{index}'

                    self.headers.append(col_name)
                    self.columns[index].name = col_name
        else:
            # Use provided headers when no header rows exist
            if self.headers and len(self.headers) == self.column_count:
                for index, col_name in enumerate(self.headers):
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
        """Generate a regex pattern representing the table structure."""
        if not self:
            return ""

        lst: List[str] = []
        does_prev_col_has_empty_cell = False
        divider_pat = f' *{re.escape(self.column_divider)} *'
        divider_leading_pat = f'{re.escape(self.column_divider)} *'
        divider_trailing_pat = f' *{re.escape(self.column_divider)}'

        for column in self.columns:
            has_empty_cell = does_prev_col_has_empty_cell or column.has_empty_cell
            if self.has_divider:
                if lst:
                    lst.append(divider_pat)
            else:
                sep_pat = PATTERN.SPACE if has_empty_cell else PATTERN.SPACES
                if lst:
                    lst.append(sep_pat)

            lst.append(column.to_regex())
            does_prev_col_has_empty_cell = column.has_empty_cell

        if self.is_start_with_divider:
            lst.insert(0, divider_leading_pat)
        if self.is_leading:
            lst.insert(0, ' *')
        if self.is_end_with_divider:
            lst.append(divider_trailing_pat)
        if self._is_trailing:
            lst.append(' *')

        return text.join_string(*lst)

    def get_header_lines_snippet(self) -> str:
        """Extract header lines snippet."""
        headers_lines = self.raw_header_rows or self.header_lines
        lst: List[str] = []

        for line in text.get_list_of_lines(*headers_lines):
            is_line_of_puncts = bool(re.match(f" *{PATTERN.PUNCTS_PHRASE} *$", line))
            is_header_line = text.Line.has_data(line) and not is_line_of_puncts
            if is_header_line:
                lst.append(line)

        return text.join_string(*lst, separator="\n")

    def to_template_snippet(self) -> str:
        """Generate a template snippet representing the table."""
        if not self:
            return ""

        snippets: List[str] = []
        headers_snippet = self.get_header_lines_snippet()
        if self.has_header_row and headers_snippet:
            snippets.append(headers_snippet)

        self.build_last_column_snippet(snippets)
        self.build_first_column_snippet(snippets)
        self.build_other_column_snippet(snippets)

        return text.join_string(*snippets, separator="\n")

    def build_first_column_snippet(self, snippets: List[str]) -> None:
        """
        Build template snippets for the case where the first column
        contains special metadata or indices.
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
                if self.last_column_data_info and index == self.column_count - 1:
                    kwargs.update(added_list_meta_data=True)

                col_snippet = column.to_template_snippet(**kwargs)
                parts.append(col_snippet if int(bit) else space_snippet)

            sep = self.divider_snippet if self.has_divider else "  "
            next_snippet = text.join_string(*parts, separator=sep)

            if self.has_divider:
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

            snippets.append(first_snippet)
            snippets.append(next_snippet)

    def build_last_column_snippet(self, snippets):
        if not self.last_column_data_info:
            return

        leading_snippet = 'start(space)' if self.is_leading else 'start()'

        first_snippet = self.first_column.to_template_snippet(to_bared_snippet=True)
        if self.has_divider:
            first_snippet = f'{self.divider_leading_snippet}{first_snippet}'
        snippets.append(f'{leading_snippet} {first_snippet}optional_spaces() -> continue.record')

        indices = self.last_column_data_info.get('indices', [])
        layouts = []
        for row in self.rows:
            if row.line in indices:
                row.row_layout not in layouts and layouts.append(row.row_layout)

        for layout in sorted(layouts, reverse=True):
            parts = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width
                if m == n:
                    m = n - 4 if (n - 4) > 2 else abs(n - 2)
                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = dict()
                if index == self.column_count - 1:
                    kwargs.update(added_list_meta_data=True)
                col_snippet = column.to_template_snippet(**kwargs)

                if int(bit) or self.has_divider:
                    parts.append(col_snippet if int(bit) else space_snippet)
                    continue

                if not parts:
                    parts.append(space_snippet)
                    continue

                last_item = parts[-1]
                pat = r'space[(]repetition_(?P<m>\d+)_(?P<n>\d+)[)]$'
                match = re.match(pat, last_item)
                if match:
                    m, n = int(match.group('m')), int(match.group('n'))
                    m += column.width
                    n += column.max_width - column.max_edge_leading_width
                    if m == n:
                        m = n - 4 if (n - 4) > 2 else abs(n - 2)
                    extend_space_snippet = f'space(repetition_{m}_{n})'
                    if parts:
                        parts.pop()
                    parts.append(extend_space_snippet)
                else:
                    parts.append(space_snippet)

            sep = self.divider_snippet if self.has_divider else "  "
            line_snippet = text.join_string(*parts, separator=sep)
            if self.has_divider:
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
            snippets.append(line_snippet)

        last_snippet = self.last_column.to_template_snippet(skipped_empty=True, added_list_meta_data=True)
        m, n = self.last_column_data_info.get('spacers')
        m = n - 4 if (n - 4) > 0 else m
        spacer_snippet = f'start() space(repetition_{m}_{n+2}) {last_snippet} end(space) -> continue'
        snippets.append(spacer_snippet)

    def build_other_column_snippet(self, snippets: List[str]) -> None:
        """
        Build template snippets for rows that are neither first-column
        nor last-column special cases.
        """
        leading_snippet = 'start(space)' if self.is_leading else 'start()'
        trailing_snippet = 'end(space) -> record' if self.is_trailing else 'end() -> record'

        first_indices = self.first_column_data_info.get('indices', [])
        last_indices = self.last_column_data_info.get('indices', [])

        # Layouts for rows that are not part of either special-case group
        layouts = [
            row.row_layout
            for row in self.rows
            if row.line not in first_indices and row.line not in last_indices
        ]

        for layout in sorted(layouts, reverse=True):
            parts = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width

                # Adjust equal-width columns
                m = n - 2 if m == n and m > 1 else m

                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = dict()
                if self.last_column_data_info and index == self.column_count - 1:
                    kwargs.update(added_list_meta_data=True)
                col_snippet = column.to_template_snippet(**kwargs)

                # If bit is 1 or divider is present → direct append
                if int(bit) or self.has_divider:
                    parts.append(col_snippet if int(bit) else space_snippet)
                    continue

                # Merge adjacent space blocks
                if not parts:
                    parts.append(space_snippet)
                    continue

                last_item = parts[-1]
                pat = r'space[(]repetition_(?P<m>\d+)_(?P<n>\d+)[)]$'
                match = re.match(pat, last_item)
                if not match:
                    parts.append(space_snippet)
                    continue

                m, n = int(match.group('m')), int(match.group('n'))
                m += column.width
                n += column.max_width - column.max_edge_leading_width
                extend_space_snippet = f'space(repetition_{m}_{n})'
                parts.pop()
                parts.append(extend_space_snippet)

            sep = self.divider_snippet if self.has_divider else "  "

            line_snippet = text.join_string(*parts, separator=sep)
            if self.has_divider:
                line_snippet = (f'{self.divider_leading_snippet}{line_snippet}'
                                f'{self.divider_trailing_snippet}')

            # Ending: end(space) -> record
            space_end_pat = r' *space[(]repetition_\d+_\d+[)] *$'
            line_snippet = (
                re.sub(space_end_pat, ' end(space) -> record', line_snippet)
                if re.search(space_end_pat, line_snippet) else
                f'{line_snippet} {trailing_snippet}'
            )

            # Leading start()
            space_any_pat = r' *space[(]repetition_\d+_\d+[)] *'
            line_snippet = (
                f'start() {line_snippet}'
                if re.match(space_any_pat, line_snippet) else
                f'{leading_snippet} {line_snippet}'
            )

            # Normalize spacing around space() blocks
            space_between_pat = r' +(space[(]repetition_\d+_\d+[)]) +'
            line_snippet = re.sub(space_between_pat, r' \1 ', line_snippet)

            # Ensure uniqueness
            is_line_snippet_existed = False
            pattern = r'(?i) *start\(\w*\) *(?P<chk>.+) *end\(\w*\) -> (record|continue)'
            match = re.match(pattern, line_snippet)
            if match:
                baseline_chk = match.group('chk')
                for snippet_ in snippets:
                    if is_line_snippet_existed:
                        break
                    other_match = re.match(pattern, snippet_)
                    if other_match:
                        is_line_snippet_existed = other_match.group('chk') == baseline_chk
            if not is_line_snippet_existed:
                snippets.append(line_snippet)


class Cell(RuntimeException):
    """
    Represents a single cell in a tabular text row.
    """

    def __init__(self, line: str, left_pos: int, right_pos: int, reference: "Cell" = None):
        self.args = (line, left_pos, right_pos, reference)

        # Positional flags
        self._leading = None
        self._trailing = None

        # Boundaries
        self.left = 0
        self.right = 0
        self.inner_left = 0
        self.inner_right = 0

        # Raw content
        self.line = ""
        self.data = ""

        # Reference cell (alignment / inheritance)
        self.reference = None

        self.process()

    def __bool__(self):
        """Return True if the cell has valid boundaries, otherwise False."""
        return self.left >= 0 or self.right > self.left

    def __len__(self) -> int:
        """Return 1 if the cell has valid boundaries, otherwise 0."""
        return int(self.left >= 0 or self.right > self.left)

    def __repr__(self) -> str:
        """Return a string representation with text, data, and boundaries."""
        cls_name = datatype.get_class_name(self)
        return f"{cls_name}(text={self.text!r}, data={self.data!r}, left={self.left}, right={self.right})"

    def __str__(self) -> str:
        """Return a string representation with text, data, and boundaries."""
        cls_name = datatype.get_class_name(self)
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
        return self._leading or ""

    @property
    def trailing(self) -> str:
        """Return trailing spaces of the cell content."""
        if self._trailing is None:
            if self.is_empty:
                self._trailing = ""
            else:
                matches = re.findall(' +$', self.data)
                self._trailing = matches[0] if matches else ""
        return self._trailing or ""

    @property
    def is_empty(self) -> bool:
        """Return True if the cell contains no text."""
        return self.text == ""

    @property
    def items_count(self) -> int:
        """Return the number of items (words) in the cell."""
        return 0 if self.is_empty else len(re.split(PATTERN.SPACES, self.text))

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
    def is_leading(self) -> bool: return self.leading != ""
    @property
    def is_single_leading(self) -> bool: return self.leading == " "
    @property
    def is_multi_leading(self) -> bool: return len(self.leading) > 1

    @property
    def is_trailing(self) -> bool: return self.trailing != ""
    @property
    def is_single_trailing(self) -> bool: return self.trailing == " "
    @property
    def is_multi_trailing(self) -> bool: return len(self.trailing) > 1

    @property
    def is_just_chars(self) -> bool:
        """Return True if the cell contains only characters without spaces."""
        return not self.is_empty and not bool(re.findall(PATTERN.WS, self.text))

    @property
    def is_group_of_chars(self) -> bool:
        """Return True if the cell contains multiple characters separated by spaces."""
        return self.text.strip() and bool(re.findall(PATTERN.WS, self.text.strip()))

    @property
    def is_containing_space(self) -> bool: return bool(re.findall(PATTERN.WS, self.text))
    @property
    def is_not_containing_space(self) -> bool: return not bool(re.findall(PATTERN.WS, self.text))
    @property
    def is_containing_spaces(self) -> bool: return bool(re.findall(r"\s\s+", self.text))

    # -----------------------------
    # Position and adjustment
    # -----------------------------

    def update_position(self, side: str, value: int = 0) -> None:
        """Update left or right boundary and reprocess the cell."""
        side = "left" if side.lower() == "left" else "right"
        setattr(self, side, value)
        self.process()

    def get_possible_prefix(self) -> str:
        """Return possible prefix before the last space in the text."""
        if self.is_empty or self.is_trailing:
            return ""
        *chk, prefix = self.text.rsplit(" ", maxsplit=1)
        return "" if chk else prefix

    def get_postfix_data(self) -> str:
        """Return postfix data after the last space or double space."""
        if self.is_multi_trailing or not self.is_containing_space:
            return ""

        # Choose the correct separator: double-space or single-space
        sep = "  " if self.is_containing_spaces else " "
        _, tail = str.rsplit(self.text, sep, maxsplit=1)
        result = f"{tail}{self.trailing}"

        # If no reference cell, return directly
        if not self.reference:
            return result

        # Compare right boundary with reference
        remaining_right = self.right - len(result)
        if remaining_right > self.reference.inner_right:
            return result

        # Try a second-level split if the tail still contains spaces
        if " " in tail:
            _, tail2 = str.rsplit(tail, " ", maxsplit=1)
            return f"{tail2}{self.trailing}"
        return ""

    def adjust_from_previous(self, prev_cell: "Cell" = None) -> None:
        """Adjust boundaries based on possible prefix of the previous cell."""
        if not isinstance(prev_cell, self.__class__):
            return

        prefix = prev_cell.get_possible_prefix()
        if not prefix or self.is_leading:
            return

        shift = len(prefix)
        self.left -= shift
        prev_cell.right -= shift

        self.process()
        prev_cell.process()

    def readjust(self, prev_cell: "Cell" = None) -> None:
        """Shift boundaries based on postfix data extracted from the previous cell."""
        if not isinstance(prev_cell, self.__class__):
            # skip adjustment
            return

        if (
            prev_cell.is_multi_trailing
            or prev_cell.is_empty
            or (prev_cell.is_single_trailing and self.is_leading)
        ):
            # skip adjustment
            return

        postfix = previous.get_postfix_data()
        if not postfix:
            return

        shift = len(postfix) + 1
        self.update_position("left", value=self.left - shift)
        previous.update_position("right", value=self.right - shift)

    def process(self) -> None:
        """Validate positions and initialize cell data."""
        line, left_pos, right_pos, ref_cell = self.args

        # Validate numeric boundaries

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

        # Reset cached flags

        self._leading = None
        self._trailing = None

        # Validate reference cell
        if isinstance(ref_cell, self.__class__) or ref_cell is None:
            self.reference = ref_cell
        else:
            cls_name = datatype.get_class_name(self)
            self.raise_runtime_error(
                msg=(
                    f"Invalid reference_cell type detected in {cls_name}.\n"
                    f"Object: {self!r}\n"
                    "Hint: Ensure the reference cell is initialized with a supported type."
                )
            )

        # Compute boundaries
        self.left = left
        self.right = len(line) if self.reference and right == 999999 else right

        # Extract raw content
        self.line = line
        self.data = self.line[self.left:self.right]

        # Compute inner boundaries based on leading/trailing whitespace
        self.inner_left = self.left + len(self.leading)
        self.inner_right = self.right - len(self.trailing)

    def set_data(self, data: str) -> None:
        """Update the cell's content and reset cached whitespace metadata."""
        self.data = data
        self._leading = None
        self._trailing = None


class Row(RuntimeException):
    """Represents a row in a tabular text structure."""

    def __init__(self, line: str, reference_row: "Row" = None, aligned: bool = True):
        self._is_puncts_group = None
        self.aligned = aligned
        self.line = line
        self.reference_row = reference_row
        self.row_layout = ""
        self.cells = []
        self.process()

    def __bool__(self) -> bool: return True if self.cells else False

    def __len__(self) -> int: return int(bool(self.cells))

    def __repr__(self) -> str: return str(self)

    def __str__(self) -> str:
        """Return a string representation with the number of columns."""
        return f"{self.__class__.__name__}(column_count={len(self.cells)})"

    @property
    def cell_count(self) -> int:
        """Number of cells in the row."""
        return len(self.cells)

    @property
    def column_count(self) -> int:
        """Alias for `cells_count`."""
        return self.cell_count

    @property
    def is_puncts_group(self) -> bool:
        """Return True if the row consists only of symbols."""
        if self._is_puncts_group is None:
            if not self.cells:
                return False
            # pattern = ' *%(p)s( +%(p)s)* *$' % dict(p=PATTERN.PUNCTS)
            pattern = rf" *{PATTERN.PUNCTS}( +{PATTERN.PUNCTS})* *$"
            self._is_puncts_group = bool(re.match(pattern, self.line))
        return self._is_puncts_group

    def append_new_cell(self, left_pos: int, right_pos: int) -> "Cell":
        """Create a new cell for this row, align it with the reference row, and append it."""

        index = len(self.cells)

        reference_cell = self.reference_row.cells[index] if self.reference_row else None
        cell = Cell(self.line, left_pos, right_pos, reference=reference_cell)

        if self.reference_row and self.reference_row.aligned:
            prev_cell = self.cells[-1] if index else None
            cell.adjust_from_previous(prev_cell=prev_cell)

        self.cells.append(cell)
        return cell

    def process(self) -> None:
        """Initialize cells based on the reference row."""
        self.cells.clear()
        if not self.reference_row:
            return

        for ref_cell in self.reference_row.cells:
            cell = self.append_new_cell(ref_cell.left, ref_cell.right)
            bit = 1 if cell.text else 0
            self.row_layout += str(bit)

    # -----------------------------
    # Reference row creation methods
    # -----------------------------

    @classmethod
    def create_reference_row(
        cls,
        line: str,
        pattern: str,
        tokens: list[str],
        aligned: bool = True
    ) -> "Row":
        """Construct a reference row from parsed tokens and boundary positions."""
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
        prev_right, last_cell = 0, None

        for item in tokens:
            left = prev_right

            # First token: compute its true position in the line
            if last_cell is None:
                prev_right = line.index(item)

            # Subsequent tokens: boundaries follow sequentially
            right = prev_right + len(item)
            prev_right = right

            last_cell = ref_row.append_new_cell(left, right)

        # Mark the final cell as open-ended
        if last_cell:
            last_cell.right = 999999

        return ref_row

    @classmethod
    def create_reference_row_from_findall(
            cls,
            line: str,
            pattern: str,
            column_count: int = -1,
    ) -> "Row":
        """Create a reference row by extracting tokens with regex findall."""
        tokens = re.findall(pattern, line)
        total = len(tokens)

        if column_count > 0 and column_count != total:
            RuntimeException.do_raise_runtime_error(
                obj=f"{cls.__name__}RTError",
                msg=(
                    f"Column count mismatch in {cls.__name__}.\n"
                    f"Parsed columns: {total} | Expected columns: {column_count}\n"
                    f"Pattern: {pattern!r}\n"
                    f"Line: {line!r}\n"
                    "Hint: Verify the input line matches the expected pattern structure."
                ),
            )

        return cls.create_reference_row(line, pattern, tokens)

    @classmethod
    def create_reference_row_from_split(
        cls,
        line: str,
        separator: str,
        column_count: int = 1
    ) -> "Row":
        """Create a reference row by splitting the line on a separator and normalizing edge cases."""
        pattern = re.escape(separator)
        tokens = re.split(pattern, line)
        total = len(tokens)

        # Handle edge cases with prefix/postfix separators
        if total == column_count + 2:
            prefix, first = tokens.pop(0), tokens.pop(0)
            tokens.insert(0, text.join_string(prefix, first, separator=separator))

            postfix, last = tokens.pop(), tokens.pop()
            tokens.append(text.join_string(last, postfix, separator=separator))
            total = len(tokens)

        # Handle single prefix or postfix separator

        elif total == column_count + 1:
            if line.strip().startswith(separator):
                prefix, first = tokens.pop(0), tokens.pop(0)
                tokens.insert(0, text.join_string(prefix, first, separator=separator))
            elif line.strip().endswith(separator):
                postfix, last = tokens.pop(), tokens.pop()
                tokens.append(text.join_string(last, postfix, separator=separator))
            total = len(tokens)

        # Validate final token count

        if column_count > 0 and column_count != total:
            RuntimeException.do_raise_runtime_error(
                obj=f"{cls.__name__}RTError",
                msg=(
                    f"Column count mismatch in {cls.__name__}.\n"
                    f"Parsed columns: {total}\n"
                    f"Expected columns: {column_count}\n"
                    f"Pattern: {pattern!r}\n"
                    f"Line: {line!r}\n"
                    "Hint: Ensure the input line matches the expected pattern structure."
                ),
            )

        return cls.create_reference_row(line, pattern, tokens, aligned=False)

    @classmethod
    def create_reference_row_by_variable(cls, line: str, pattern: str) -> "Row":
        """Create a reference row using regex named groups (v000, v001, ...)."""
        match = re.match(pattern, line)
        result = match.groupdict() if match else {}
        tokens = [result.get(f"v{i:03d}") for i in range(256) if f"v{i:03d}" in result]

        return cls.create_reference_row(line, pattern, tokens)

    @classmethod
    def do_creating_reference_row(cls, line: str, pattern: str, case: str = "", column_count: int = -1) -> "Row":
        """Factory method to create a reference row using different parsing strategies."""

        if case == "findall":
            return cls.create_reference_row_from_findall(line, pattern, column_count)

        if case == "variable":
            return cls.create_reference_row_by_variable(line, pattern)

        if case == "split":
            return cls.create_reference_row_from_split(line, pattern, column_count)

        return RuntimeException.do_raise_runtime_error(
            obj=f"{cls.__name__}RTError",
            msg=(
                f"Unsupported case encountered in do_creating_reference_row.\n"
                f"Case value: {case!r}\n"
                f"Class: {cls.__name__}\n"
                "Hint: Verify that the provided case is valid and supported."
            ),
        )


class Column:
    """Represents a single column in a tabular text structure."""

    def __init__(
        self,
        index=0,
        name="",
        left_column=None,
        right_column=None,
        is_last=False
    ):

        # Structural relationships
        self.left_column = left_column
        self.right_column = right_column
        self.is_last = is_last

        # Identity
        self.index = index
        self.name = name or f"col{index}"

        # Data and metadata
        self.extra_data = None
        self.cells = []

        # Boundaries
        self.left_border = 0
        self.right_border = 0

        # Alignment state
        self._alignment = "left"

    def __bool__(self) -> bool: return True if self.cells else False

    def __len__(self) -> int: return int(bool(self.cells))

    def __str__(self) -> str:
        """Return a string representation of the column with name and cell count."""
        return f"{self.__class__.__name__}(name={self.name!r}, cells_count={len(self.cells)})"

    def __repr__(self) -> str: return str(self)

    @property
    def cells_count(self) -> int: return len(self.cells)

    @property
    def rows_count(self) -> int: return self.cells_count

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
            return 0

        max_width = max(widths)
        if len(set(widths)) == 1:
            return max_width

        left_positions = {cell.left for cell in self.cells}
        right_positions = {cell.right for cell in self.cells}

        if len(left_positions) == 1:
            common_width, _ = Counter(widths).most_common().pop(0)
            return max_width if common_width == max_width else math.ceil(statistics.mean(widths))
        elif len(right_positions) == 1:
            return max_width
        return math.ceil(statistics.mean(widths))

    @property
    def max_edge_trailing_width(self) -> int:
        """Maximum trailing width contributed by the right column."""
        if not self.right_column:
            return 0

        trailing_lengths = [
            len(text.Line.get_leading(cell.data))
            for cell in self.right_column.cells
            if cell.data.strip()
        ]
        if not trailing_lengths:
            return 0

        edge_width = max(trailing_lengths)
        return 0 if self.right_column.width == edge_width else edge_width

    @property
    def max_edge_leading_width(self) -> int:
        """Maximum leading width contributed by the left column."""
        if not self.left_column:
            return 0

        leading_lengths = [
            len(text.Line.get_trailing(cell.data))
            for cell in self.left_column.cells
            if cell.data.strip()
        ]
        if not leading_lengths:
            return 0

        edge_width = max(leading_lengths)
        return 0 if self.left_column.width == edge_width else edge_width

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

        key = f"{int(len(left_edges) == 1)}{int(len(right_edges) == 1)}"
        alignment_map = {"11": "left", "10": "left", "01": "right", "00": "center"}
        self._alignment = alignment_map.get(key, "left")

    def to_regex(self) -> str:
        """Generate a regex pattern for the column based on its cells."""
        if not self:
            return ""

        texts = [cell.text for cell in self.cells if cell.text]
        if self.extra_data:
            texts.extend(self.extra_data)

        node = PatternTranslator.do_factory_create(*texts)
        pattern = node.get_regex_pattern(var=self.name)

        if node.is_group() and not self.is_last:
            max_items = max(cell.items_count for cell in self.cells)
            occurrence = max_items - 1
            if occurrence > 0:
                pattern = f"{pattern[:-2]}{{,{occurrence}}})"

        if self.has_empty_cell:
            first, last = str.split(pattern, ">", maxsplit=1)
            pattern = f"{first}>( {{{self.width},{self.max_width}}})|( *{last[:-1]} *))"

        return pattern

    def to_template_snippet(
        self,
        added_list_meta_data: bool = False,
        skipped_empty: bool = False,
        to_bared_snippet: bool = False,
    ) -> str:
        """Generate a template snippet for the column."""
        if not self:
            return ""

        texts = [cell.text for cell in self.cells if cell.text]
        if self.extra_data:
            texts.extend(self.extra_data)

        node = PatternTranslator.do_factory_create(*texts)
        kwargs = {} if to_bared_snippet else {"var": self.name}
        snippet = node.get_template_snippet(**kwargs)

        if to_bared_snippet or (skipped_empty and not added_list_meta_data):
            return snippet

        if node.is_group() and not self.is_last:
            max_items = max(cell.items_count for cell in self.cells)
            occurrence = max_items - 1
            if occurrence > 0:
                if "_phrase" in snippet or re.match(r"(mixed_)?words", snippet):
                    fmt = "%s, at_most_%s_phrase_occurrences)"
                else:
                    fmt = "%s, at_most_%s_group_occurrences)"
                snippet = node.singular_name + "(" + snippet.split("(", 1)[-1]
                snippet = fmt % (snippet[:-1], occurrence)

        if added_list_meta_data:
            snippet = f"{snippet[:-1]}, meta_data_list)"

        return snippet
