"""
textfsmgen.engine.common
========================

Common grammar pattern utilities for the TextFSM Generator framework.
"""

import re
from typing import Optional, Union
from copy import deepcopy

import yaml

from textfsmgen.core.patterns import TextPattern
from textfsmgen.libs import PATTERN
from textfsmgen.libs import number
from textfsmgen.libs import text

from textfsmgen.engine.translate import PatternTranslator

from textfsmgen.exceptions import RuntimeException
from textfsmgen.exceptions import raise_exception

def get_line_position_by(
    lines: list[str],
    item: Optional[Union[str, int, None]]
) -> Optional[int]:
    """
    Determine the position of a line in `lines` based on a string
    pattern or numeric index.
    """
    if item is None:
        return None

    is_number, index = number.try_to_get_number(item, return_type=int)
    if is_number:
        return None if index >= len(lines) else index

    regex_prefix = r'(?i)^\s*--regex\s+'

    if re.match(regex_prefix, str(item)):
        pattern = re.sub(regex_prefix, "", str(item))
    else:
        pattern = TextPattern(item)

    for index, line in enumerate(lines):
        if re.search(pattern, line, re.I):
            return index

    return None


def get_fixed_line_snippet(lines: list[str], line: str = "", index: Optional[int] = None) -> str:   # noqa
    """
    Generate a normalized snippet representation of a line.
    """
    # Resolve line by index if provided
    if index is not None:
        is_number, converted_index = number.try_to_get_number(index, return_type=int)
        if is_number:
            try:
                line = lines[converted_index]   # noqa
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
        ws_type = "whitespace" if line.strip(" ") else "space"
        return f"start() end({ws_type})"

    # Tokenize and normalize numeric tokens
    tokens = text.Text(line.strip()).do_finditer_split(PATTERN.NON_WSS)
    for i, token in enumerate(tokens):
        if token.strip():
            factory = PatternTranslator.do_factory_create(token)
            if factory.name in {"digit", "digits", "number", "mixed_number", "puncts"}:
                tokens[i] = factory.to_snippet()

    snippet_body = text.join_string(*tokens)
    leading = text.Line.get_leading(line)
    trailing = text.Line.get_trailing(line)

    return f"{leading}{snippet_body}{trailing}"


def sanitize_identifier(value: str, fallback: str = "col", lower: bool = True) -> str:
    """
    Normalize an identifier by converting a trailing '%' into '_pct',
    removing other percent signs, collapsing noise characters, and
    stripping leading digits and underscores.
    """
    if not value:
        return fallback

    # Normalize percent suffix
    pct = "_pct_".join(value.rsplit("%", maxsplit=1))
    pct = pct.replace("%", "")

    # Collapse punctuation and symbol noise
    noise = r"[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+"
    cleaned = re.sub(noise, "_", pct).strip("_")

    # Prevent leading digits
    cleaned = re.sub(r"^\d+", "_", cleaned)

    return cleaned.lower() if lower else cleaned


def apply_replacements(data: str, rules=None) -> str:
    """
    Apply string replacement rules to multi-line text. Rules may be provided as:
    - YAML string containing a list of [old, new] pairs or a dict of {key: {old, new}}
    - A list/tuple of [old, new] pairs
    - A dict whose values are {old, new} mappings
    """
    if not data or not rules:   # noqa
        return data

    # Normalize rules: YAML string -> Python object
    if isinstance(rules, str):
        if "fallback(" in rules.lower():
            return apply_fallback_replacements(data, rules)

        parsed = yaml.safe_load(rules)
        if not parsed:
            return data
        if not isinstance(parsed, (list, tuple)):
            raise ValueError("YAML must define a list of pairs or a dict of {old,new} mappings.")
        rules = parsed

    # Validate and normalize list/tuple of pairs
    if isinstance(rules[0], (list, tuple)):
        if not all(isinstance(pair, (list, tuple)) and len(pair) == 2 for pair in rules):
            raise ValueError("Expected a list/tuple of [old, new] pairs.")
        pairs = [(old, new) for old, new in rules]

    # Validate and normalize dict of {key: {old,new}}
    elif isinstance(rules[0], dict):
        if not all(isinstance(v, dict) and "curr" in v and "new" in v for v in rules):
            raise ValueError("Expected element of the list form {'curr': ..., 'new': ...}.")
        pairs = [(v["curr"], v["new"]) for v in rules]

    elif isinstance(rules, (list, tuple)) and len(rules) == 2:
        pairs = [deepcopy(rules)]

    elif isinstance(rules, dict) and "curr" in rules and "new" in rules:
        pairs = [(rules.get("curr"), rules.get("new"))]

    else:
        raise ValueError("Rules must be a YAML string, list/tuple of pairs.")

    # Apply replacements line-by-line
    output_lines = []   # noqa
    for line in data.splitlines():
        for old, new in pairs:
            if old in line:
                line = line.replace(old, new)
        if line.strip():
            output_lines.append(line)

    return "\n".join(output_lines) if output_lines else data


def apply_fallback_replacements(data: str, rules=None) -> str:
    """
    Apply fallback(var_name, keyword) replacements to the given text.

    Extracts fallback(...) patterns from the provided rules (YAML string,
    list, or tuple), builds unique (var_name, keyword) pairs, and rewrites
    matching segments in the input text.
    """
    parsed = yaml.safe_load(rules)
    if not parsed:
        return data

    pattern = r"(?i)fallback[(]\s*var_\w+\s*,\s*\w+\s*[)]"
    matches = []

    # Collect fallback(...) expressions from rules
    if isinstance(parsed, str):
        matches.extend(re.findall(pattern, parsed))
    elif isinstance(parsed, (list, tuple)):
        for item in parsed:
            matches.extend(re.findall(pattern, str(item)))

    if not matches:
        return data

    # Build unique (var_name, keyword) pairs
    pairs = []
    for expr in matches:
        _, var_name, keyword, _ = re.split(r"[)(,]+", expr)
        pair = (var_name, keyword)
        if pair not in pairs:
            pairs.append(pair)

    output = []
    for line in data.splitlines():
        cursor = 0
        for var_name, keyword in pairs:
            pat = rf"(?i)\w+(?P<body>[(]\s*{var_name}\s*[^)]*[)])"
            match = re.search(pat, line[cursor:])
            if match:
                cursor = match.end()
                original = match.group()
                replacement = keyword + match.group("body")
                line = line.replace(original, replacement)

        if line.strip():
            output.append(line)

    return "\n".join(output) if output else data