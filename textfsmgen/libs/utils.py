"""
textfsmgen.libs.utils
=====================

General-purpose utility functions used across TextFSMGen.
"""

import re
from textwrap import wrap
from pprint import pprint

from .pattern import PATTERN


def split_by_matches(text, pattern=r"(?u)\s+"):
    """Split text into alternating segments of non-matching and matching substrings."""
    parts = []
    last_end = 0

    for m in re.finditer(pattern, text):
        if m.start() > last_end:
            parts.append(text[last_end:m.start()])
        parts.append(m.group())
        last_end = m.end()

    if last_end < len(text):
        parts.append(text[last_end:])

    return parts


def extract_non_whitespace(text: str) -> list[str]:
    """Return all contiguous non‑whitespace segments from the text."""
    return re.findall(r"(?u)\S+", text)


def extract_segments(line: str, parts: list[str]):
    """Split the line into (left, matched subcontent, right) around the given parts."""
    escaped = r"\s+".join(re.escape(p) for p in parts)
    pattern = rf"(?P<left>.*?)(?P<subcontent>{escaped})(?P<right>.*)"

    match = re.search(pattern, line)
    if match:
        return (
            match.group("left"),
            match.group("subcontent"),
            match.group("right"),
        )

    return line, "", ""


def text_to_pattern(source: str, *, ignore_case: bool = True) -> str:
    """Convert a text string into a regex-safe generalized pattern."""
    token_re = rf"(?ix)\s+|[a-z]+|{PATTERN.PUNCTS}|[0-9]+"
    parts = []

    for tok in split_by_matches(source, pattern=token_re):
        if re.fullmatch(PATTERN.PUNCTS, tok):
            parts.append(re.escape(tok))
        elif tok.isdigit():
            parts.append(r"[0-9]+")
        elif tok.isspace():
            parts.append(r"\s+")
        elif re.fullmatch(r"(?i)[a-z]+", tok):
            parts.append(tok)
        else:
            parts.append(re.escape(tok))

    pattern = "".join(parts)
    if ignore_case:
        pattern = "(?i)" + pattern

    try:
        re.compile(pattern)
    except re.error as err:
        raise ValueError(f"Invalid generated regex pattern: {pattern!r}") from err

    return pattern


class TextMatcher:
    """Collect and match text patterns against input strings."""

    def __init__(self, text: str = ""):
        self._patterns = []
        self.add_pattern(text)

    def __bool__(self):
        return bool(self._patterns)

    def __len__(self):
        return 1 if self else 0

    def clear(self):
        """Remove all stored patterns."""
        self._patterns.clear()

    def add_pattern(self, text: str) -> None:
        """Convert text to a regex pattern and store it."""
        if text:
            pattern = text_to_pattern(text)
            self._patterns.append(pattern)

    def matches(self, text: str) -> bool:
        """Return True if any stored pattern matches the given text."""
        return any(re.search(pattern, text) for pattern in self._patterns)


class Tabular:
    """A utility class for constructing and displaying tabular data."""
    def __init__(self, data, missing='not_found'):
        self.result = ''
        self.data = [data] if isinstance(data, dict) else data
        self.missing = missing
        self.is_tabular = False
        self.failure = ''
        self.process()

    def __bool__(self): return self.is_tabular

    def __len__(self): return 1 if self.is_tabular else 0

    def compute_column_widths(self, columns):
        """Return max display width for each column based on data and defaults."""
        widths = {col: len(str(col)) for col in columns}

        for row in self.data:
            for col in columns:
                value = row.get(col, self.missing)
                widths[col] = max(widths[col], len(str(value)))

        return widths

    def infer_column_alignments(self) -> list[str]:
        """Infer text alignment for each column based on cell content."""

        # Build column-wise lists
        num_cols = len(self.data[0].keys())
        columns = [[] for _ in range(num_cols)]

        for row in self.data:
            for idx, value in enumerate(row.values()):
                columns[idx].append(value)

        alignments = []

        for col in columns:
            numeric_flags = []
            punct_flags = []

            for cell in col:
                text = str(cell).strip()

                if isinstance(cell, (int, float, bool)):
                    numeric_flags.append(True)
                    punct_flags.append(False)
                    continue

                if isinstance(cell, str):
                    if re.fullmatch(PATTERN.MIXED_NUMBER, text):
                        numeric_flags.append(True)
                        punct_flags.append(False)
                        continue

                    if re.fullmatch(PATTERN.PUNCTS, text):
                        numeric_flags.append(False)
                        punct_flags.append(True)
                        continue

                    if text.lower() in {"n/a", "na"}:
                        numeric_flags.append(True)
                        punct_flags.append(False)
                        continue

                numeric_flags.append(False)
                punct_flags.append(False)

            if all(numeric_flags):
                align = "right"
            elif all(punct_flags):
                align = "center"
            else:
                align = "left"

            alignments.append(align)

        return alignments


    def format_cell(self, text, width, align="left"):   # noqa
        """Return text aligned to the given width using the current justification."""
        align_mapping = {
            "left": str.ljust,
            "center": str.center,
            "right": str.rjust,
        }
        return align_mapping.get(align, "left")(text, width)

    def format_header_row(self, columns, widths, alignments):
        """Return a formatted header row using column names and computed widths."""
        cells = []
        use_align = len(alignments) == len(columns)
        for idx, col in enumerate(columns):
            align = alignments[idx] if use_align else "left"
            cells.append(self.format_cell(col, widths[col], align=align))
        return f"| {' | '.join(cells)} |"

    def format_body_rows(self, columns, widths, alignments):
        """Return formatted body rows using column values and computed widths."""
        rows = []
        use_align = len(alignments) == len(columns)
        for row in self.data:
            cells = []
            for idx, col in enumerate(columns):
                align = alignments[idx] if use_align else "left"
                value = row.get(col, self.missing)
                cells.append(self.format_cell(value, widths[col], align=align))
            rows.append(f"| {' | '.join(cells)} |")

        return "\n".join(rows)

    def process(self):
        """Assemble the full tabular output using columns, widths, and formatted rows."""

        ok, failure = validate_uniform_tabular_data(self.data)
        if not ok:
            self.failure = failure
            return

        try:
            columns = list(self.data[0].keys())
            widths = self.compute_column_widths(columns)
            alignments = self.infer_column_alignments()

            border = "+-{}-+".format(
                "-+-".join("-" * widths[c] for c in columns))
            header = self.format_header_row(columns, widths, alignments)
            body = self.format_body_rows(columns, widths, alignments)

            parts = [border, header, border, body, border]
            self.result = "\n".join(parts)
            self.is_tabular = True

        except Exception as ex:
            self.failure = f"{type(ex).__name__}: {ex}"
            self.is_tabular = False
            raise ex

    def get(self):
        """Retrieve the processed tabular output or the raw data."""
        tabular_data = self.result if self.is_tabular else self.data
        return tabular_data

    def print(self):
        """Print the tabular content or raw data."""
        tabular_data = self.get()
        if isinstance(tabular_data, (dict, list, tuple, set)):
            pprint(tabular_data)
        else:
            print(tabular_data)


def validate_uniform_tabular_data(records):
    """Validate that data is a non‑empty list of dicts with identical keys."""
    error = "records MUST be a non-empty list of dicts with identical keys."
    if not records or not isinstance(records, (list, tuple, dict)):
        return False, error

    if isinstance(records, dict):
        return True, ""

    expected_keys = None

    for record in records:
        if not isinstance(record, dict):
            return False, error
        keys = record.keys()
        if expected_keys is None:
            expected_keys = keys

        if keys != expected_keys:
            return False, error

    return True, ""


def get_data_as_tabular(data, missing="not_found", with_index=False):
    """Return a tabular string representation of structured data."""
    ok, failure = validate_uniform_tabular_data(data)
    if not ok:
        return data

    # Normalize input into a list of row dicts
    rows = data.copy() if isinstance(data, list) else [data.copy()]

    if with_index:
        indexed_rows = []
        for idx, row in enumerate(rows, start=1):
            # Only add index if not already present
            if "index" in row:
                indexed_rows.append(row.copy())
            else:
                indexed_rows.append({"index": str(idx), **row})
        rows = indexed_rows

    table = Tabular(rows, missing=missing)
    return table.get()


def print_data_as_tabular(data, missing='not_found', with_index=False):
    """Print structured data in a tabular format."""
    result = get_data_as_tabular(data, missing=missing, with_index=with_index)
    if isinstance(result, (list, tuple, dict)):
        pprint(result)
    else:
        print(result)
