"""
textfsmgen.libs.utils
====================

General-purpose utility functions used across TextFSMGen.
"""

import re

from . import PATTERN


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
    token_re = rf"(?ix)\s+|[a-z]+|{PATTERN.puncts}|[0-9]+"
    parts = []

    for tok in split_by_matches(source, pattern=token_re):
        if re.fullmatch(PATTERN.puncts, tok):
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