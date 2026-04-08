"""
textfsmgen.libs.pattern
=======================

General-purpose Patter class and functions used across TextFSMGen.
"""


import re
import string

from textfsmgen.exceptions import raise_exception, EscapePatternError
from .generic import StatusString


class PATTERN:  # noqa
    """Reusable regex fragments for common character classes."""

    # --- Generic wildcard ---
    DOT = '.'
    DOTS = '.+'
    ANYTHING = '.*'
    SOMETHING = '.+'

    # --- Literal spaces ---
    SPACE = ' '
    SPACES = ' +'

    # --- Whitespace ---
    WS = r'\s'
    WHITESPACE = r'\s'
    WSS = r'\s+'
    WHITESPACES = r'\s+'

    # --- Digits ---
    DIGIT = r'\d'
    DIGITS = r'\d+'

    # --- Numbers ---
    NUMBER = r'\d*[.]?\d+'
    NUM = r'\d*[.]?\d+'
    MIXED_NUMBER = r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'
    MIXED_NUM = r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'

    # --- letters ---
    LETTER = '[a-zA-Z]'
    LETTERS = rf'{LETTER}+'

    OPTIONAL_LETTERS_GROUP = rf'{LETTERS}(\s+{LETTERS})*'
    OPT_LETTERS_GRP = OPTIONAL_LETTERS_GROUP

    LETTERS_GROUP = rf'{LETTERS}(\s+{LETTERS})+'
    LETTERS_GRP = LETTERS_GROUP

    # --- alphabet numeric ---
    ALNUM = '[a-zA-Z0-9]'

    # --- punctuations ---
    PUNCT = r'[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    PUNCTS = r'%s+' % PUNCT

    # --- group of puncts ---
    OPTIONAL_PUNCTS_GROUP = r'%s(\s+%s)*' % (PUNCTS, PUNCTS)
    OPT_PUNCTS_GRP = OPTIONAL_PUNCTS_GROUP

    PUNCTS_GROUP = r'%s(\s+%s)+' % (PUNCTS, PUNCTS)
    PUNCTS_GRP = PUNCTS_GROUP

    SPACE_PUNCT = r'[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    SP = r'[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'

    LETTER_PUNCT = r'[a-zA-Z\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    LP = r'[a-zA-Z\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'

    # --- Visible characters ---
    GRAPH = r'[\x21-\x7e]'

    # --- word ---
    WORD = r'[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*'

    # --- group of word ---
    WORDS = r'%s(\s+%s)*' % (WORD, WORD)
    OPTIONAL_WORD_GROUP = WORDS
    OPT_WORD_GRP = WORDS

    WORD_GROUP = r'%s(\s+%s)+' % (WORD, WORD)
    WORD_GRP = WORD_GROUP

    # --- mixed-words ----
    MIXED_WORD = r'[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*'

    # --- group of mixed-word ---
    MIXED_WORDS = r'%s(\s+%s)*' % (MIXED_WORD, MIXED_WORD)
    OPTIONAL_MIXED_WORD_GROUP = MIXED_WORDS
    OPT_MIXED_WORD_GRP = MIXED_WORDS

    MIXED_WORD_GROUP = r'%s(\s+%s)+' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GRP = MIXED_WORD_GROUP

    # --- Non-whitespace(s) ---
    NON_WS = r'\S'
    NON_WHITESPACE = r'\S'
    NON_WSS = r'\S+'
    NON_WHITESPACES = r'\S+'

    # --- group of non-whitespace(s) ---
    OPTIONAL_NON_WSS_GROUP = r'%s(\s+%s)*' % (NON_WSS, NON_WSS)
    OPT_NON_WSS_GRP = OPTIONAL_NON_WSS_GROUP

    NON_WSS_GROUP = r'%s(\s+%s)+' % (NON_WSS, NON_WSS)
    NON_WSS_GRP = NON_WSS_GROUP

    OPTIONAL_NON_WHITESPACES_GROUP = r'%s(\s+%s)*' % (NON_WSS, NON_WSS)
    OPT_NON_WHITESPACES_GRP = OPTIONAL_NON_WHITESPACES_GROUP

    NON_WHITESPACES_GROUP = r'%s(\s+%s)+' % (NON_WSS, NON_WSS)
    NON_WHITESPACES_GRP = NON_WHITESPACES_GROUP

    @classmethod
    def resolve_subset(cls, key):
        """Return the subset name associated with the given key."""
        subsets = {
            "OPTIONAL_NON_WSS_GROUP": "NON_WSS",
            "OPT_NON_WSS_GRP": "NON_WSS",
            "NON_WSS_GROUP": "NON_WSS",
            "NON_WSS_GRP": "NON_WSS",
            "NON_WSS": "NON_WSS",

            "OPTIONAL_NON_WHITESPACES_GROUP": "NON_WHITESPACES",
            "OPT_NON_WHITESPACES_GRP": "NON_WHITESPACES",
            "NON_WHITESPACES_GROUP": "NON_WHITESPACES",
            "NON_WHITESPACES_GRP": "NON_WHITESPACES",
            "NON_WHITESPACES": "NON_WHITESPACES",

            "OPTIONAL_MIXED_WORD_GROUP": "MIXED_WORD",
            "OPT_MIXED_WORD_GRP": "MIXED_WORD",
            "MIXED_WORD_GROUP": "MIXED_WORD",
            "MIXED_WORD_GRP": "MIXED_WORD",
            "MIXED_WORDS": "MIXED_WORD",
            "MIXED_WORD": "MIXED_WORD",

            "OPTIONAL_WORD_GROUP": "WORD",
            "OPT_WORD_GRP": "WORD",
            "WORD_GROUP": "WORD",
            "WORD_GRP": "WORD",
            "WORDS": "WORD",
            "WORD": "WORD",

            "OPTIONAL_PUNCTS_GROUP": "PUNCTS",
            "OPT_PUNCTS_GRP": "PUNCTS",
            "PUNCTS_GROUP": "PUNCTS",
            "PUNCTS_GRP": "PUNCTS",

            "OPTIONAL_LETTERS_GROUP": "LETTERS",
            "OPT_LETTERS_GRP": "LETTERS",
            "LETTERS_GROUP": "LETTERS",
            "LETTERS_GRP": "LETTERS",
        }
        return subsets.get(key.upper(), "")



class ParsedKeywordMappingName:
    def __init__(self, name: str, default=None):
        self._default = default
        self._name = str(name)

        self._keyword = ''
        self._pattern = ''
        self._is_parsed = False

        self._parse()

    def __bool__(self): return self._is_parsed

    def __len__(self): return 1 if self._is_parsed else 0

    @property
    def name(self): return self._name

    @property
    def keyword(self): return self._keyword

    @property
    def pattern(self): return self._pattern or PATTERN.OPTIONAL_NON_WSS_GROUP

    def _apply(self, pattern):
        if not pattern:
            return
        self._is_parsed = True
        self._keyword = self._name.lower()
        self._pattern = pattern

    def _parse(self):
        self._load_defined_pattern()
        self._apply_optional()
        self._apply_some()
        self._apply_exact()
        self._apply_range()

    @classmethod
    def to_digit(cls, value):
        """Convert a numeric word to its digit string if possible."""
        text = str(value).lower()

        words = {
            "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
            "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10,
        }

        if text.isdigit():
            return value

        if text in words:
            return str(words[text])

        return value

    @classmethod
    def in_group(cls, name, index=0):
        """Return True if the name belongs to the specified group or any group."""
        groups = [
            (  # group 0
                "DOT",
                "SPACE", "WS", "WHITESPACE",
                "DIGIT", "LETTER", "ALNUM", "PUNCT",
                "SP", "SPACE_PUNCT",
                "LP", "LETTER_PUNCT",
                "GRAPH", "NON_WS", "NON_WHITESPACE",
            ),
            (  # group 1
                "DOTS", "SPACES", "WSS", "WHITESPACES",
                "DIGITS", "LETTERS", "PUNCTS",
                "NON_WSS", "NON_WHITESPACES",
            ),
            (  # group 2
                "NUMBER", "NUM",
                "MIXED_NUMBER", "MIXED_NUM",
                "WORD", "MIXED_WORD",
            ),
            (  # group 3
                "OPTIONAL_LETTERS_GROUP",
                "OPTIONAL_PUNCTS_GROUP",
                "OPTIONAL_WORD_GROUP", "WORDS",
                "OPTIONAL_MIXED_WORD_GROUP",
                "OPTIONAL_NON_WSS_GROUP",
                "OPTIONAL_NON_WHITESPACES_GROUP",
            ),
        ]

        key = name.upper()

        if 0 <= index < len(groups):
            return key in groups[index]

        for group in groups:
            if key in group:
                return True

        return False

    @classmethod
    def _resolve_defined(cls, name):
        """Return the PATTERN constant matching the given name."""
        return getattr(PATTERN, name.upper(), None)

    def _load_defined_pattern(self):
        """Resolve and apply the defined pattern for this instance."""
        pattern = self._resolve_defined(self._name)
        self._apply(pattern)

    def _apply_optional(self):
        """Apply the optional form of a defined pattern if matched."""
        key = self._name
        if self._is_parsed:
            return

        m = re.fullmatch(r"(?i)optional_(?P<name>\w+)", key)
        if not m:
            return

        base = m.group("name").lower()
        pattern = self._resolve_defined(base)
        if not pattern:
            return

        # group 0 → single-char patterns
        if self.in_group(base, index=0):
            self._apply(rf"{pattern}?")
            return

        # group 1 → plural patterns ending with '+'
        if self.in_group(base, index=1):
            self._apply(rf"{pattern[:-1]}*")
            return

        # group 2 or 3 → grouped patterns
        if self.in_group(base, index=2) or self.in_group(base, index=3):
            self._apply(rf"({pattern})?")

    def _apply_some(self):
        """Apply the 'one or more' form of a defined pattern if matched."""
        if self._is_parsed:
            return

        m = re.fullmatch(r"(?i)some_(?P<name>\w+)", self._name)
        if not m:
            return

        base = m.group("name").lower()
        pattern = self._resolve_defined(base)
        if not pattern:
            return

        # group 0 → single‑unit patterns (use '+')
        if self.in_group(base, index=0):
            self._apply(rf"{pattern}+")
            return

        # groups 1–3 → already plural or grouped (use as‑is)
        if (
                self.in_group(base, index=1)
                or self.in_group(base, index=2)
                or self.in_group(base, index=3)
        ):
            self._apply(pattern)

    def _apply_exact(self):
        """Apply an exact-count pattern form if the name matches."""
        if self._is_parsed:
            return

        m = re.fullmatch(r"(?i)(?P<value>[0-9]+|[a-z]+)_?(?P<name>\w+)", self._name)
        if not m:
            return

        raw = m.group("value").lower()
        count = self.to_digit(raw)
        base = m.group("name").lower()
        pattern = self._resolve_defined(base)

        if not pattern or not count.isdigit():
            return

        # group 0 → single-unit patterns
        if self.in_group(base, index=0):
            self._apply(rf"{pattern}{{{count}}}")
            return

        # plural/grouped patterns → subtract 1 for the repeated tail
        n = int(count) - 1

        if self.in_group(base, index=1) or self.in_group(base, index=2):
            if n >= 0:
                self._apply(rf"{pattern}(\s+{pattern}){{{n}}}")
                return
            self._apply(pattern)
            return

        if self.in_group(base, index=3):
            subset = PATTERN.resolve_subset(base)
            if not subset:
                return

            if n >= 0:
                self._apply(rf"{subset}(\s+{subset}){{{n}}}")
                return
            self._apply(pattern)

    def _apply_range(self):
        """Apply a ranged repetition form if the name encodes a range."""
        if self._is_parsed:
            return

        m = re.fullmatch(
            r"(?i)(?P<left>[a-z0-9]*)_(to_)?(?P<right>[a-z0-9]*)_(?P<name>\w+)",
            self._name
        )
        if not m:
            return

        left_raw = m.group("left").lower() or "0"
        right_raw = m.group("right").lower() or "999"
        right_raw = "999" if right_raw == "n" else right_raw

        lo = self.to_digit(left_raw)
        hi = self.to_digit(right_raw)

        base = m.group("name").lower()
        pattern = self._resolve_defined(base)

        if not pattern or not lo.isdigit() or not hi.isdigit():
            return

        if int(hi) <= int(lo):
            return

        # group 0 → single-unit patterns
        if self.in_group(base, index=0):
            lo = "" if lo == "0" else lo
            hi = "" if hi == "999" else hi
            self._apply(rf"{pattern}{{{lo},{hi}}}")
            return

        lo = 0 if int(lo) - 1 <= 0 else int(lo) - 1
        hi = 0 if int(hi) - 1 <= 0 else int(hi) - 1

        lo = str(lo) if lo else ""
        hi = "" if hi == 998 else str(hi)

        # groups 1–2 → plural or mixed patterns
        if self.in_group(base, index=1) or self.in_group(base, index=2):
            self._apply(rf"{pattern}(\s+{pattern}){{{lo},{hi}}}")
            return

        # group 3 → subset-based patterns
        if self.in_group(base, index=3):
            subset = PATTERN.resolve_subset(base)
            if not subset:
                return
            self._apply(rf"{subset}(\s+{subset}){{{lo},{hi}}}")


def resolve_pattern(name, default=None):
    """Return the resolved regex pattern for the given name."""
    fallback = default or PATTERN.OPTIONAL_NON_WSS_GROUP
    mapping = ParsedKeywordMappingName(name)
    return mapping.pattern or fallback


def resolve_keyword(name):
    """Return the normalized keyword associated with the given name."""
    mapping = ParsedKeywordMappingName(name)
    return mapping.keyword


def validate_pattern(pattern: str, flags: int = 0, exception_cls=None):
    """Compile a regex pattern or raise a custom exception."""
    exception_cls = exception_cls or Exception
    try:
        return re.compile(pattern, flags=flags)
    except re.error as ex:
        raise_exception(ex, cls=exception_cls)


def is_valid_pattern(pattern):
    """Return a StatusString describing whether the input is a valid regex."""
    if not isinstance(pattern, str):
        msg = (f"Pattern must be a string, "
               f"but received <{type(pattern).__name__}:{pattern}> instead.)")
        return StatusString(msg, False)
    try:
        result = re.compile(pattern)
        return StatusString(str(result), bool(result))
    except Exception as ex:
        return StatusString(str(ex), False)


def soft_escape(pattern: str, validate: bool = True) -> str:
    """Escape only required regex metacharacters while preserving normal punctuation."""
    text = str(pattern)

    punct_or_space = string.punctuation + " "
    special_regex_chars = "^$.?*+|{}[]()\\"

    result = []
    for ch in text:
        esc = re.escape(ch)
        if ch in punct_or_space:
            result.append(esc if ch in special_regex_chars else ch)
        else:
            result.append(esc)

    escaped = "".join(result)

    if validate:
        validate_pattern(escaped, exception_cls=EscapePatternError)

    return escaped
