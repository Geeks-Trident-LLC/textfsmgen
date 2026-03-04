"""
textfsmgen.libs.common
======================

General-purpose Patter class and functions used across TextFSMGen.
"""


import re
import string

from textfsmgen.exceptions import raise_exception, EscapePatternError
from .generic import StatusString


class PATTERN:
    """Reusable regex fragments for common character classes."""

    # --- Generic wildcard ---
    ANYTHING = '.'
    ANY = '.'
    ZERO_OR_ONE = '.?'
    SOMETHING = '.*'
    ZERO_OR_MORE = '.*'
    EVERYTHING = '.+'
    ONE_OR_MORE = '.+'

    # --- Literal spaces ---
    SPACE = ' '
    SPACES = ' +'
    ZERO_OR_SPACE = ' ?'
    ZERO_OR_SPACES = ' *'
    ZERO_OR_MORE_SPACE = ' *'
    AT_LEAST_ONE_SPACE = SPACES
    MORE_THAN_ONE_SPACE = '  +'
    STARTS_WITH_SPACE = '^ '
    STARTS_WITH_SPACES = '^ +'
    ENDS_WITH_SPACE = ' $'
    ENDS_WITH_SPACES = ' +$'

    # --- Whitespace ---
    WS = r'\s'
    ZERO_OR_WSS = r'\s*'
    ZERO_OR_MORE_WS = r'\s*'
    WSS = r'\s+'
    ONE_OR_WSS = r'\s+'
    ONE_OR_MORE_WS = r'\s+'

    # --- Newlines / CRLF ---
    CRNL = r'\r?\n|\r'
    CR_NL = CRNL
    NEWLINE = CRNL
    ZERO_OR_MORE_CRLF = r'[\r\n]*'
    ZERO_OR_MORE_NEWLINE = ZERO_OR_MORE_CRLF
    NEWLINES = ZERO_OR_MORE_NEWLINE
    ONE_OR_MORE_CRLF = r'[\r\n]+'
    ONE_OR_MORE_NEWLINE = ONE_OR_MORE_CRLF

    # --- Digits ---
    DIGIT = r'\d'
    ZERO_OR_DIGIT = r'\d?'
    ZERO_OR_DIGITS = r'\d*'
    DIGITS = r'\d+'
    ONE_OR_MORE_DIGITS = r'\d+'
    AT_LEAST_ONE_DIGIT = r'\d+'

    # --- Numbers ---
    NUMBER = r'\d*[.]?\d+'
    ZERO_OR_NUMBER = rf'{NUMBER}?'
    MIXED_NUMBER = r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'
    ZERO_OR_MIXED_NUMBER = rf'{MIXED_NUMBER}?'

    # --- letters ---
    LETTER = '[a-zA-Z]'
    ZERO_OR_LETTER = rf'{LETTER}?'
    ZERO_OR_LETTERS = rf'{LETTER}*'
    ZERO_OR_MORE_LETTERS = ZERO_OR_LETTERS
    LETTERS = rf'{LETTER}+'
    ONE_OR_MORE_LETTERS = LETTERS
    AT_LEAST_ONE_LETTER = LETTERS

    # --- alphabet numeric ---
    ALPHABET_NUMERIC = '[a-zA-Z0-9]'
    ZERO_OR_ALPHABET_NUMERIC = rf'{ALPHABET_NUMERIC}?'
    ZERO_OR_MORE_ALPHABET_NUMERIC = rf'{ALPHABET_NUMERIC}*'
    ONE_OR_MORE_ALPHABET_NUMERIC = rf'{ALPHABET_NUMERIC}+'
    AT_LEAST_ONE_ALPHABET_NUMERIC = rf'{ALPHABET_NUMERIC}+'

    # --- punctuations ---
    PUNCT = r'[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    PUNCTS = r'%s+' % PUNCT

    # --- group of puncts ---
    PUNCT_GROUP = r'%s( %s)*' % (PUNCTS, PUNCTS)
    PUNCT_GROUP_SPACES = r'%s( +%s)*' % (PUNCTS, PUNCTS)
    PUNCTS_PHRASE = r'%s( %s)+' % (PUNCTS, PUNCTS)
    PUNCT_PHRASE_SPACES = r'%s( +%s)+' % (PUNCTS, PUNCTS)

    # --- group of puncts separated by whitespace ---
    PUNCT_GROUP_SEP_WS = r'%s(\s%s)*' % (PUNCTS, PUNCTS)
    PUNCT_GROUP_SEP_WSS = r'%s(\s+%s)*' % (PUNCTS, PUNCTS)
    PUNCTS_PHRASE_SEP_WS = r'%s(\s%s)+' % (PUNCTS, PUNCTS)
    PUNCT_PHRASE_SEP_WSS = r'%s(\s+%s)+' % (PUNCTS, PUNCTS)

    # --- puncts check ---

    ENDS_WITH_PUNCT = r'%s$' % PUNCT
    ENDS_WITH_PUNCTS = r'%s$' % PUNCTS
    ENDS_WITH_PUNCT_GROUP = ' *%s *$' % PUNCT_PHRASE_SPACES

    SPACE_OR_PUNCT = r'[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    SPACES_OR_PUNCTS = r'%s+' % SPACE_OR_PUNCT

    # --- Visible characters ---
    GRAPH = r'[\x21-\x7e]'
    ZERO_OR_GRAPH = rf'{GRAPH}?'
    ZERO_OR_MORE_GRAPH = rf'{GRAPH}*'
    ONE_OR_MORE_GRAPH = rf'{GRAPH}+'

    # --- word ---
    WORD = r'[a-zA-Z][a-zA-Z0-9]*'

    # --- group of word ---
    WORDS = r'%s( %s)*' % (WORD, WORD)
    WORD_GROUP = WORDS
    PHRASE = r'%s( %s)+' % (WORD, WORD)

    WORDS_SEP_SPACES = r'%s( +%s)*' % (WORD, WORD)
    WORD_GROUP_SEP_SPACES = WORDS_SEP_SPACES
    PHRASE_SEP_SPACES = r'%s( +%s)+' % (WORD, WORD)

    # --- group of word separated by whitespace---
    WORDS_SEP_WS = r'%s(\s%s)*' % (WORD, WORD)
    PHRASE_SEP_WS = r'%s(\s%s)+' % (WORD, WORD)

    WORDS_SEP_WSS = r'%s(\s+%s)*' % (WORD, WORD)
    WORD_GROUP_SEP_WSS = WORDS_SEP_WSS
    PHRASE_SEP_WSS = r'%s(\s+%s)+' % (WORD, WORD)

    # --- mixed-words ----
    MIXED_WORD = r'[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*'

    # --- group of mixed-word ---
    MIXED_WORDS = r'%s( %s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GROUP = MIXED_WORDS
    MIXED_PHRASE = r'%s( %s)+' % (MIXED_WORD, MIXED_WORD)

    MIXED_WORDS_SEP_SPACES = r'%s( +%s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GROUP_SEP_SPACES = MIXED_WORDS_SEP_SPACES
    MIXED_PHRASE_SEP_SPACES = r'%s( +%s)+' % (MIXED_WORD, MIXED_WORD)

    # --- group of mixed-word separated by whitespace ---
    MIXED_WORDS_SEP_WS = r'%s(\s%s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GROUP_SEP_WS = MIXED_WORDS_SEP_WS
    MIXED_PHRASE_SEP_WS = r'%s(\s%s)+' % (MIXED_WORD, MIXED_WORD)

    MIXED_WORDS_SEP_WSS = r'%s(\s+%s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GROUP_SEP_WSS = MIXED_WORDS_SEP_WSS
    MIXED_PHRASE_SEP_WSS = r'%s(\s+%s)+' % (MIXED_WORD, MIXED_WORD)

    # --- Non-whitespace(s) ---
    NON_WS = r'\S'
    ZERO_OR_ONE_NON_WS = rf'{NON_WS}?'
    ZERO_OR_MORE_NON_WSS = rf'{NON_WS}*'
    NON_WSS = rf'{NON_WS}+'

    # --- group of non-whitespace(s) ---
    NON_WS_GROUP = r'%s( %s)*' % (NON_WSS, NON_WSS)
    NON_WS_PHRASE = r'%s( %s)+' % (NON_WSS, NON_WSS)

    NON_WS_GROUP_SEP_SPACES = r'%s( +%s)*' % (NON_WSS, NON_WSS)
    NON_WS_PHRASE_SEP_SPACES = r'%s( +%s)+' % (NON_WSS, NON_WSS)

    # --- group of non-whitespace(s) separated by whitespace ---
    NON_WS_GROUP_SEP_WS = r'%s(\s%s)*' % (NON_WSS, NON_WSS)
    NON_WS_PHRASE_SEP_WS = r'%s(\s%s)+' % (NON_WSS, NON_WSS)

    NON_WS_GROUP_SEP_WSS = r'%s(\s+%s)*' % (NON_WSS, NON_WSS)
    NON_WS_PHRASE_SEP_WSS = r'%s(\s+%s)+' % (NON_WSS, NON_WSS)


def lookup_pattern(name, default=None):
    """Retrieve a regex pattern constant by name."""
    fallback = PATTERN.NON_WS_GROUP_SEP_SPACES
    default = default or fallback
    attr = name.upper()
    pattern = getattr(PATTERN, attr, default)
    return pattern


def validate_pattern(
    pattern: str,
    flags: int = 0,
    exception_cls: Optional[Type[Exception]] = None
) -> Optional[re.error | None]:
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
