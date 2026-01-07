"""
textfsmgen.gpcommon
===================

Common grammar pattern utilities for the TextFSM Generator framework.

This module provides shared helper functions and abstractions used across
grammar pattern (GP) modules. It centralizes logic for locating line
positions, normalizing line snippets, and handling common transformations
such as whitespace detection and numeric token substitution.

Purpose
-------
- Provide reusable utilities for grammar pattern processing.
- Simplify line position detection using regex, wildcard, or numeric criteria.
- Normalize line snippets into template‑friendly representations.
- Support consistent handling of whitespace, digits, and mixed numbers.

Notes
-----
- This module is typically used internally by `textfsmgen.gp` and related
  modules, but can be imported directly for advanced customization.
- Empty lines are represented with explicit start/end markers and whitespace
  classification.
- Numeric tokens (digits, numbers, mixed numbers) are automatically
  translated into template snippets via `TranslatedPattern`.
"""

import re

from regexapp import TextPattern
from genericlib import Misc, STRING, Wildcard, PATTERN, Text
from textfsmgen.gp import TranslatedPattern

from textfsmgen.exceptions import RuntimeException
from textfsmgen.exceptions import raise_exception

def get_line_position_by(lines: list[str], item: str | int | None) -> int | None:
    """
    Determine the position of a line in `lines` based on a string
    pattern or numeric index.

    Parameters
    ----------
    lines : list of str
        The list of lines to search.
    item : str or int
        Search criteria. Can be:
        - A string containing regex or wildcard directives.
        - A numeric index (int or string convertible to int).

    Returns
    -------
    int or None
        The index of the matching line, or None if not found.

    Notes
    -----
    - Strings prefixed with ``--regex`` or ``--wildcard`` are
      interpreted accordingly.
    - Numeric values beyond the length of `lines` return None.
    """
    if item is None:
        return None

    regex_prefix = r'(?i)^\s*--regex\s+'
    wildcard_prefix = r'(?i)^\s*--wildcard\s+'
    if Misc.is_string(item):
        if re.search(regex_prefix, item):
            pattern = re.sub(regex_prefix, STRING.EMPTY, item)
        elif re.search(wildcard_prefix, item):
            txt = re.sub(wildcard_prefix, STRING.EMPTY, item)
            pattern = Wildcard(txt, from_start_to_end=False).pattern
        else:
            pattern = TextPattern(item)

        for index, line in enumerate(lines):
            if re.search(pattern, line, re.I):
                return index
    else:
        is_number, index = Misc.try_to_get_number(item, return_type=int)
        if is_number:
            return None if index >= len(lines) else index

    return None


def get_fixed_line_snippet(lines: list[str], line: str = "", index: int | None = None) -> str:
    """
    Generate a normalized snippet representation of a line.

    This function extracts a line either directly (via the `line` argument)
    or by index from the provided list of lines. It then normalizes the line
    into a template snippet representation:

    - Empty lines are represented as ``start() end(space|whitespace)``.
    - Digits, numbers, and mixed numbers are replaced with template
      placeholders via `TranslatedPattern`.
    - Leading and trailing whitespace are preserved using `Misc.get_leading_line`
      and `Misc.get_trailing_line`.

    Parameters
    ----------
    lines : list of str
        The list of lines to extract from.
    line : str, optional
        The line to process. Ignored if `index` is provided.
    index : int, optional
        Index of the line in `lines` to process. Must be a valid integer.

    Returns
    -------
    str
        A snippet representation of the line, with numeric tokens replaced
        by template placeholders.

    Raises
    ------
    UnknownParamIndexTypeError
        If `index` is not an integer.
    UnknownParamLineTypeError
        If `line` is not a string or bytes.
    RuntimeError
        If `index` is out of range or another unexpected error occurs.
    """
    # Resolve line by index if provided
    if index is not None:
        is_number, converted_index = Misc.try_to_get_number(index, return_type=int)
        if is_number:
            try:
                line = lines[converted_index]
            except IndexError as ex:
                total = len(lines)
                msg = (
                    f"Index out of range: attempted to access index {converted_index}, "
                    f"but only {total} lines are available."
                )
                raise_exception(ex, msg=msg)
            except Exception as ex:
                RuntimeException.do_raise_runtime_error(ex)
        else:
            RuntimeException.do_raise_runtime_error(
                obj="UnknownParamIndexTypeError",
                msg=(
                    f"Invalid index type: expected an integer to access list, "
                    f"but received {type(index).__name__} ({index!r})."
                ),
            )

    # Decode bytes to string if necessary
    if isinstance(line, bytes):
        line = line.decode("utf-8")

    # Validate type
    if not isinstance(line, str):
        RuntimeException.do_raise_runtime_error(
            obj="UnknownParamLineTypeError",
            msg=(
                f"Invalid line type: expected a string, "
                f"but received {type(line).__name__} with value {line!r}."
            ),
        )

    # Handle empty or whitespace-only lines
    if not line.strip():
        ws_type = "whitespace" if line.strip(STRING.SPACE_CHAR) else "space"
        return f"start() end({ws_type})"

    # Tokenize and normalize numeric tokens
    tokens = Text(line.strip()).do_finditer_split(PATTERN.NON_WHITESPACES)
    for i, token in enumerate(tokens):
        if token.strip():
            factory = TranslatedPattern.do_factory_create(token)
            if factory.name in {"digit", "digits", "number", "mixed_number", "puncts"}:
                tokens[i] = factory.get_template_snippet()

    snippet_body = Misc.join_string(*tokens)
    leading = Misc.get_leading_line(line)
    trailing = Misc.get_trailing_line(line)

    return f"{leading}{snippet_body}{trailing}"
