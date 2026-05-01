"""
textfsmgen.libs.text
====================

Enhanced string and text-processing utilities.
"""

import typing
from typing import Any, Tuple, Optional

import re
import string
import time
import random

import textwrap

from textfsmgen.exceptions import LineArgumentError
from textfsmgen.exceptions import EscapePatternError


class BaseText(str):
    """A string subclass that provides enhanced text representation."""
    def __new__(cls, *args, **kwargs):
        arg0 = args[0] if args else None
        if args and isinstance(arg0, BaseException):
            txt = super().__new__(cls, f'{type(arg0).__name__}: {arg0}')    # noqa
            return txt
        else:
            txt = super().__new__(cls, *args, **kwargs)     # noqa
            return txt


class Text(BaseText):
    """A string subclass with extended text formatting and utility methods."""  # noqa
    @classmethod
    def format(cls, *args, **kwargs):
        """
        Safely format text using old-style (`%`) or new-style (`str.format`)
        string formatting.
        """
        if not args:
            text = ''
            return text
        else:
            if kwargs:
                fmt = args[0]
                try:
                    text = str(fmt).format(args[1:], **kwargs)
                    return text
                except Exception as ex:
                    text = cls(ex)
                    return text
            else:
                if len(args) == 1:
                    text = cls(args[0])
                    return text
                else:
                    fmt = args[0]
                    t_args = tuple(args[1:])
                    try:
                        if len(t_args) == 1 and isinstance(t_args[0], dict):
                            text = str(fmt) % t_args[0]
                        else:
                            text = str(fmt) % t_args

                        if text == fmt:
                            text = str(fmt).format(*t_args)
                        return text
                    except Exception as ex1:
                        try:
                            text = str(fmt).format(*t_args)
                            return text
                        except Exception as ex2:
                            text = '%s\n%s' % (cls(ex1), cls(ex2))
                            return text

    @classmethod
    def wrap_html(cls, tag, data, *args):
        """
        Wrap text content in an HTML element.
        """
        data = str(data)
        tag = str(tag).strip()
        attributes = [str(arg).strip() for arg in args if str(arg).strip()]
        if attributes:
            attrs_txt = " ".join(attributes)
            if data.strip():
                result = '<{0} {1}>{2}</{0}>'.format(tag, attrs_txt, data)
            else:
                result = '<{0} {1}/>'.format(tag, attrs_txt)
        else:
            if data.strip():
                result = '<{0}>{1}</{0}>'.format(tag, data)
            else:
                result = '<{0}/>'.format(tag)
        return result

    def do_finditer_split(self, pattern):
        """
        Split the string into segments based on regex matches.
        """
        result = []
        start = 0
        m = None
        for m in re.finditer(pattern, self):
            pre_match = self[start:m.start()]
            match = m.group()
            result.append(pre_match)
            result.append(match)
            start = m.end()

        if m:
            post_match = self[m.end():]
            result.append(post_match)
        else:
            result.append(str(self))
        return result


class BaseLine(str):
    """
    A string subclass representing a single line of text with preserved metadata.
    """
    def __new__(cls, data, *args):
        line_obj = super().__new__(cls, data)  # noqa
        lines = line_obj.splitlines(keepends=True)
        if len(lines) > 1:
            raise LineArgumentError(
                "The 'data' argument contains multiple lines; expected a single line."
            )
        line = lines[0] if lines else ""
        line_obj._raw_data = line

        match_data = re.match(r"([^\r\n]+)?", line)
        line_obj._data = match_data.group() if match_data else ""

        match_joiner = re.search(r"([\r\n]+)?$", line)
        line_obj._joiner = match_joiner.group() if match_joiner else ""
        return line_obj


class Line(BaseLine):   # noqa
    """
    A specialized string subclass representing a single line of text with
    additional utilities for whitespace handling, validation, and regex-based
    pattern conversion.
    """
    @property
    def joiner(self): return self._joiner

    @property
    def raw_data(self): return self._raw_data

    @property
    def raw(self): return self._raw_data

    @property
    def data(self): return self.strip()

    @property
    def clean_line(self): return self.strip()

    @property
    def is_empty(self): return self == ""

    @property
    def is_optional_empty(self): return bool(re.fullmatch(r"\s+", self))

    @property
    def leading(self): return self[:len(self) - len(self.lstrip())]

    @property
    def trailing(self): return self[len(self.rstrip()):] if self.clean_line else ""

    @property
    def is_leading(self) -> bool: return len(self.leading) > 0

    @property
    def is_trailing(self) -> bool: return len(self.trailing) > 0

    @property
    def is_whitespace_leading(self):
        return bool(re.search(r"\s+", self.leading))

    @property
    def is_ws_leading(self): return self.is_whitespace_leading

    @property
    def is_whitespace_trailing(self):
        return bool(re.search(r"\s+", self.trailing))

    @property
    def is_ws_trailing(self): return self.is_whitespace_trailing

    @classmethod
    def is_line(cls, data, on_failure=False):
        """Validate whether the given data represents a single line of text."""
        lines = str(data).splitlines(keepends=True)
        if len(lines) == 1 or len(lines) == 0:
            return True

        if on_failure:
            error = ("The 'data' argument contains multiple lines; "
                     "it must be a single line.")
            raise LineArgumentError(error)

        return False

    @classmethod
    def has_leading(
        cls, line: str,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> bool:
        """Return True if line has leading whitespace."""
        return cls.get_leading(line, start=start, end=end) != ""

    @classmethod
    def has_trailing(
        cls, line: str,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> bool:
        """Return True if line has trailing whitespace."""
        return cls.get_trailing(line, start=start, end=end) != ""

    @classmethod
    def get_leading(
        cls, line: str,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> str:
        """Extract leading whitespace from line."""
        _, line_ = try_to_str(line, allow_none=True)
        line = cls(str(line_)[start:end])
        return line.leading

    @classmethod
    def get_trailing(
        cls, line: str,
        start: Optional[int] = None,
        end: Optional[int] = None
    ) -> str:
        """Extract trailing whitespace from line."""
        _, line_ = try_to_str(line, allow_none=True)
        line = cls(str(line_[start:end]))
        return line.trailing

    @classmethod
    def has_data(cls, line):
        """Check whether a line of text contains non-whitespace characters."""
        _, line_ = try_to_str(line, allow_none=True)
        return bool(re.search(r'\S+', str(line_)))

    @classmethod
    def has_whitespace_in_line(cls, line):
        """Check whether a line of text contains internal whitespace sequences."""
        _, line_ = try_to_str(line, allow_none=True)
        return any(re.findall(r"[^ \S\r\n]+", str(line_)))

    def convert_to_regex_pattern(self) -> str:
        """Convert the line into a regex-compatible pattern string."""  # noqa
        result = []
        punct_pat = BaseMatchedObject.punctuation_pattern
        pat = f'({punct_pat}+ +)\\1+'
        other_pat = r'\s+'
        if re.search(pat, self):
            items = self.do_finditer_split(self, pattern=pat)
            for item in items:
                if isinstance(item, (PreMatchedObject, PostMatchedObject)):
                    lst = self.do_finditer_split(item.data, pattern=other_pat)
                    result.extend(lst)
                else:
                    result.append(item)
        elif re.search(other_pat, self):
            result = self.do_finditer_split(self, pattern=other_pat)
        else:
            result = [BaseMatchedObject(self)]
        text_pattern = ''.join(elmt.to_pattern() for elmt in result)
        return text_pattern

    def do_finditer_split(self, data, pattern=r'\s+'):  # noqa
        """Split a string into matched and unmatched segments
        using regex finditer."""    # noqa
        result = []
        start = 0
        match = None
        for match in re.finditer(pattern, data):
            pre_obj = PreMatchedObject(match, start)
            not pre_obj.is_empty and result.append(pre_obj)

            matched_obj = MatchedObject(match)
            result.append(matched_obj)
            start = match.end()

        if match is not None:
            post_obj = PostMatchedObject(match, start)
            not post_obj.is_empty and result.append(post_obj)
        else:
            result.append(BaseMatchedObject(data))
        return result


class BaseMatchedObject:    # noqa
    """
    Represents a fragment of matched text and converts it into the most
    appropriate regular‑expression pattern.
    """
    punctuation_pattern = r'[!\"#$%&\'()*+,./:;<=>?@\[\\\]\^_`{|}~-]'
    repeated_punctuation_pattern = f'({punctuation_pattern}+?)\\1+'
    repeated_punctuations_space_pattern = f'({punctuation_pattern}+ +)\\1+'
    default_separator = ''
    user_separator = ''

    def __init__(self, match):
        self.match = match if isinstance(match, re.Match) else None
        self.data = match if isinstance(match, str) else ''

    @property
    def is_empty(self):
        """Indicates whether the data of matched object contains any text."""
        return self.data == ''

    def change_separator(self, separator=' ', user_pattern=''):
        """
        Updates the whitespace‑normalization behavior for this matched object.
        """
        self.user_separator = user_pattern
        self.default_separator = separator

    def to_pattern(self):
        """
        Returns the most appropriate regular‑expression fragment for this matched
        object.
        """
        result = dict()
        result.update(self.get_whitespace_pattern())    # noqa
        result.update(self.get_repeated_puncts_space_pattern())
        result.update(self.get_repeated_puncts_pattern())
        result.update(self.get_text_pattern())
        pattern = [key for key, value in result.items() if value][0]
        return pattern

    def get_whitespace_pattern(self):
        """
        Generates a regex fragment representing a run of whitespace characters.
        """
        if not re.match(r'\s+$', self.data):
            return {'': False}

        if self.user_separator:
            return self.user_separator, True

        total = len(self.data)
        is_space = self.data[0] == ' ' and len(set(self.data)) == 1
        if self.default_separator:
            pattern = self.default_separator
        else:
            pattern = ' ' if is_space else r'\s'
        pattern = f'{pattern}+' if total > 1 else pattern

        return {pattern: True}

    def get_text_pattern(self):
        """
        Produces a regex fragment that matches the text exactly as it appears.
        """
        pattern = do_soft_regex_escape(self.data)
        return {pattern: True}

    def get_repeated_puncts_pattern(self):
        """
        Generates a regex fragment for sequences composed entirely of punctuation,
        with special handling for repeated punctuation runs.
        """
        if not re.match(f'{self.punctuation_pattern}+$', self.data):
            return {'': False}
        else:
            start, m, pattern = 0, None, ''
            for m in re.finditer(self.repeated_punctuation_pattern, self.data):
                pattern += do_soft_regex_escape(self.data[start:m.start()])
                found = m.group()
                repeated = str.join('', dict(zip(found, found)))
                fmt = '%s{2,}' if len(repeated) == 1 else '(%s){2,}'
                pattern += fmt % do_soft_regex_escape(repeated)
                start = m.end()
            else:
                if m:
                    pattern += do_soft_regex_escape(self.data[m.end():])
                    return {pattern: True}
                else:
                    pattern = do_soft_regex_escape(self.data)
                    return {pattern: True}

    def get_repeated_puncts_space_pattern(self):
        """
        Generates a regex fragment for sequences where punctuation characters are
        repeatedly followed by one or more spaces.
        """
        match = re.match(f'{self.repeated_punctuations_space_pattern}$', self.data)
        if not match:
            return {'': False}
        found = match.groups()[0]
        puncts_pat = do_soft_regex_escape(found.strip())
        space_pat = ' +' if '  ' in found else ' '
        pattern = '(%s%s){2,}' % (puncts_pat, space_pat)
        return {pattern: True}


class MatchedObject(BaseMatchedObject):
    """
    Specialized matched‑text wrapper that always derives its content from a
    regular‑expression match object.
    """
    def __init__(self, match):
        super().__init__(match)
        self.data = match.group()


class PreMatchedObject(BaseMatchedObject):
    """Represents the text that appears immediately before a regex match."""
    def __init__(self, match, start):
        super().__init__(match)
        self.data = match.string[start: match.start()]


class PostMatchedObject(BaseMatchedObject):
    """
    Represents the text that appears immediately after a regex match.
    """
    def __init__(self, match, start):
        super().__init__(match)
        self.data = match.string[start:]


def get_generic_error_msg(instance, fmt, *other):
    """
    Constructs a standardized error message string for the given instance.
    """
    args = ['%sError' % instance.__class__.__name__]
    args.extend(other)
    new_fmt = '%%s - %s' % fmt
    err_msg = new_fmt % tuple(args)
    return err_msg


def get_whitespace_chars(k=8, to_list=True):
    """
    Returns all Unicode characters within the range 0 to 2**k that are
    recognized as whitespace by the regular‑expression engine.
    """
    lst = [chr(i) for i in range(pow(2, k)) if re.search(r"\s", chr(i))]
    return frozenset(lst) if to_list else str.join('', lst)


ASCII_WHITESPACE_CHARS = get_whitespace_chars(k=8, to_list=True)
ASCII_WHITESPACE_STRING = get_whitespace_chars(k=8, to_list=False)
WHITESPACE_CHARS = get_whitespace_chars(k=16, to_list=True)
WHITESPACE_STRING = get_whitespace_chars(k=16, to_list=False)


def get_non_whitespace_chars(k=8, to_list=True):
    """
    Returns all Unicode characters within the range 0 to 2**k that are *not*
    recognized as whitespace by the regular‑expression engine.
    """
    lst = [chr(i) for i in range(pow(2, k)) if not re.search(r"\s", chr(i))]
    return frozenset(lst) if to_list else str.join('', lst)


ASCII_NON_WHITESPACE_CHARS = get_non_whitespace_chars(k=8, to_list=True)
ASCII_NON_WHITESPACE_STRING = get_non_whitespace_chars(k=8, to_list=False)
NON_WHITESPACE_CHARS = get_non_whitespace_chars(k=16, to_list=True)
NON_WHITESPACE_STRING = get_non_whitespace_chars(k=16, to_list=False)


def do_soft_regex_escape(pattern: Any) -> str:
    """
    Perform a controlled, "soft" escaping of characters for use in regular expressions.
    """
    _, value = try_to_str(pattern, allow_none=True)
    text = str(value)

    all_punct = string.punctuation + " "
    regex_metachars = "^$.?*+|{}[]()\\"

    result: list[str] = []
    for char in text:
        escaped = re.escape(char)
        if char in all_punct:
            result.append(escaped if char in regex_metachars else char)
        else:
            result.append(escaped)

    new_pattern = "".join(result)

    try:
        re.compile(new_pattern)
    except re.error as e:
        raise EscapePatternError(f"Invalid escaped pattern: {new_pattern}") from e

    return new_pattern


def enclose_string(text: Any, quote: str = '"', is_new_line: bool = False) -> str:
    """
    Enclose the given text in single or triple quotes, with optional newline formatting.
    """
    if quote not in {"'", '"'}:
        quote = '"'

    _, value = try_to_str(text, allow_none=True)
    text = str(value)
    escaped_text = text.replace(quote, "\\" + quote)

    if "\n" in text or "\r" in text:
        fmt = f"{quote*3}\n%s\n{quote*3}" if is_new_line else f"{quote*3}%s{quote*3}"
        return fmt % escaped_text
    return f"{quote}{escaped_text}{quote}"


def dedent_and_strip(txt):
    """
    Convert input to string, remove common leading indentation, and strip
    leading/trailing whitespace.
    """
    _, value = try_to_str(txt, allow_none=True)
    new_txt = textwrap.dedent(str(value)).strip()
    return new_txt


def decorate_list_of_line(items: list[str]) -> str:
    """Create a framed message from a list of text lines."""
    max_len = max(len(item) for item in items)
    border = f"+-{'-' * max_len}-+"
    rows = [f"| {item.ljust(max_len)} |" for item in items]
    return "\n".join([border] + rows + [border])


def decorate_text(*parts: str) -> str:
    """Convert text parts into lines and decorate them as a framed block."""
    text = list_to_text(*parts)
    lines = text.splitlines()
    return decorate_list_of_line(lines)


def list_to_text(*args: Any) -> str:
    """Convert one or more items into a newline-separated string.
    """
    result: list[str] = []

    def flatten(item: Any) -> None:
        if isinstance(item, (list, tuple)):
            for sub_item in item:
                flatten(sub_item)
        elif isinstance(item, bytes):
            result.append(item.decode("utf-8"))
        elif isinstance(item, str):
            result.append(item)
        else:
            result.append(str(item))

    for arg in args:
        flatten(arg)

    return "\n".join(result)


def get_list_of_lines(*lines: Any) -> list[str]:
    """Convert one or more lines into a flattened list of text lines."""
    lines_out: list[str] = []

    for item in lines:
        if isinstance(item, (list, tuple)):
            # Recursively process nested sequences
            lines_out.extend(get_list_of_lines(*item))
            continue

        _, text = try_to_str(item, allow_none=True)
        lines_out.extend(re.split(r"\r?\n|\r", str(text)))

    # Normalize single empty string to empty list
    if lines_out == [""]:
        return []

    return lines_out


def get_list_of_readonly_lines(*lines: Any) -> tuple[str, ...]:
    """Convert lines into a tuple of text lines (immutable version)."""
    return tuple(get_list_of_lines(*lines))


def is_string(obj):
    """Check whether the given object is a string."""
    return isinstance(obj, typing.Text)


def is_string_or_none(obj):
    """Check whether the given object is either a string or `None`."""
    return isinstance(obj, (type(None), typing.Text))


def is_punctuation(data):
    """Return True if the text consists solely of ASCII punctuation."""
    pattern = r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+"
    return bool(re.fullmatch(pattern, data))


def try_to_str(value: Any, allow_none: bool = False) -> Tuple[bool, str]:
    """Attempt to convert input to a string; return success flag and result."""
    if allow_none and value is None:
        return True, ""
    if isinstance(value, str):
        return True, value
    if isinstance(value, bytes):
        return True, value.decode("utf-8")
    return False, value


def join_string(*inputs: Any, separator: str = "") -> str:
    """Join one or more inputs into a single string."""
    parts: list[str] = []

    for item in inputs:
        if isinstance(item, (list, tuple)):
            # Recursively process nested sequences
            parts.append(join_string(*item, separator=separator))
            continue

        _, text = try_to_str(item, allow_none=True)
        parts.append(str(text))

    # Normalize single empty string to empty result
    if parts == [""]:
        return ""
    if len(parts) == 1:
        return parts[0]

    return separator.join(parts)


def indent(*inputs: Any, width: int = 4, prefix_newline=False, suffix_newline=False) -> str:
    """Indent one or more inputs by a specified number of spaces."""
    prefix = "\n" if prefix_newline else ""
    suffix = "\n" if suffix_newline else ""
    indent_width = max(width, 0)
    text_block = "\n".join(get_list_of_lines(*inputs))
    block = f"{prefix}{text_block}{suffix}"
    return textwrap.indent(block, " " * indent_width)


def indent_level2(*inputs: Any, width: int = 2, start_pos: int = 1, other_width: int = 4) -> str:
    """Indent text with two different indentation levels."""
    start_pos = max(start_pos, 0)
    other_width = max(other_width, width)

    if start_pos == 0 or other_width == width:
        return indent(*inputs, width=width)

    lines = re.split(r"\r?\n|\r", indent(*inputs, width=0))

    first_block = textwrap.indent("\n".join(lines[:start_pos]), " " * width)
    remaining_block = textwrap.indent("\n".join(lines[start_pos:]), " " * other_width)

    return f"{first_block}\n{remaining_block}"


def is_multiline(text: Any) -> bool:
    """
    Check whether the given text contains multiple lines.
    """
    is_str, value = try_to_str(text)
    if is_str:
        return len(re.split(r"\r?\n|\r", value)) > 1
    return False


def skip_first_line(text: Any) -> str:
    """
    Return the input text without its first line.
    """

    is_str, value = try_to_str(text)
    if is_str:
        lines = re.split(r"\r?\n|\r", value)
        return "\n".join(lines[1:])
    return text


def get_first_char(value: Any, force_str: bool = True) -> str:
    """Return the first character of the input."""
    is_str, val = try_to_str(value)
    if is_str:
        return val[:1]
    return str(val)[:1] if force_str else ""


def get_last_char(value: Any, force_str: bool = True) -> str:
    """Return the last character of the input."""
    is_str, val = try_to_str(value)
    if is_str:
        return val[-1:]
    return str(val)[-1:] if force_str else ""


def escape_double_quote(value: Any) -> Any:
    """Escape double quotes in a string."""
    is_str, val = try_to_str(value)
    return val.replace('"', '\\"') if is_str else value


def escape_single_quote(value: Any) -> Any:
    """Escape single quotes in a string."""
    is_str, val = try_to_str(value)
    return val.replace("'", "\\'") if is_str else value


def escape_quote(value: Any) -> Any:
    """Escape both single and double quotes in a string."""
    is_str, val = try_to_str(value)
    return re.sub(r"(['\"])", r"\\\1", val) if is_str else value


def make_unique_id(prefix: str = "", suffix: str = "") -> str:
    """Return a unique ID composed of a timestamp and random digits."""
    timestamp = str(int(time.time()))
    rand_digits = "".join(str(d) for d in random.sample(range(10), 10))

    clean_prefix = re.sub(r"[^\w-]+", "", prefix)
    clean_suffix = re.sub(r"[^\w-]+", "", suffix)

    return f"{clean_prefix}{timestamp}{rand_digits}{clean_suffix}"


def join_text_block(text: str) -> str:
    """Join multi-line text into one line using dot/hyphen spacing rules."""
    lines = [ln.rstrip() for ln in get_list_of_lines(text) if ln.strip()]
    if not lines:
        return ""

    merged = [lines[0]]

    for curr in lines[1:]:
        prev = merged[-1]
        curr = curr.strip()
        if prev.endswith(".") or curr.startswith("."):
            sep = "  "      # two spaces
        elif prev.endswith("-") or curr.startswith("-"):
            sep = ""       # no space
        else:
            sep = " "      # one space

        merged.append(sep + curr)

    return "".join(merged)


def wrap_text_block(text: str, limit: int = 76, subject: str = "") -> str:
    """Wrap a text block with subject-aware indentation and width limits."""
    raw = text.decode("utf-8") if isinstance(text, bytes) else str(text)
    subj = str(subject)
    width = 76 if limit <= 0 else limit

    if not raw.strip():
        return raw

    line = join_text_block(raw)
    subj_len = len(subj)

    # If subject is too long relative to the limit, place wrapped text on next line
    if subj_len / width > 0.30:
        wrapped = textwrap.wrap(line, width=width - 4)
        indented = textwrap.indent("\n".join(wrapped), " " * 4)
        return f"{subj}\n{indented}"

    # Otherwise, wrap text so the first line starts after the subject
    wrapped = textwrap.wrap(line, width=width - subj_len)
    prefixes = [" " * (subj_len + 1)] * len(wrapped)
    prefixes[0] = f"{subj} "

    return "\n".join(p + w for p, w in zip(prefixes, wrapped))


def center_fixed_width(text: str) -> str:
    """Return text centered within a fixed width of 40 or 80 characters."""
    txt = text.decode("utf-8") if isinstance(text, bytes) else str(text)
    width = 40 if len(txt) < 40 else 60 if len(txt) < 60 else 80
    return txt.center(width)
