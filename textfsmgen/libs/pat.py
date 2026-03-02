"""
textfsmgen.libs.common
======================

General-purpose Patter class and functions used across TextFSMGen.
"""


import re
import string


class PATTERN:      # noqa
    """Reusable regex fragments for common character classes."""

    punct=rf"[{re.escape(string.punctuation)}]"
    puncts = rf"{punct}+"

    ANYTHING = '.'
    ZOANYTHING = '.?'
    SOMETHING = '.*'
    EVERYTHING = '.+'

    SPACE = ' '
    SPACES = ' +'
    MTONESPACES = '  +'
    MORETHANONESPACES = MTONESPACES
    ATLONESPACES = '  +'
    ATLEASTONESPACES = ATLONESPACES
    ZOSPACE = ' ?'
    ZOSPACES = ' *'
    SPACEATSOS = '^ '
    SPACESATSOS = '^ +'
    SPACEATEOS = ' $'
    SPACESATEOS = ' +$'

    WHITESPACE = r'\s'
    WHITESPACES = r'\s+'
    ZOWHITESPACES = r'\s*'

    CRNL = r'\r?\n|\r'
    CR_NL = CRNL
    MULTICRNL = r'[\r\n]+'
    ZOMULTICRNL = r'[\r\n]*'

    DIGIT = r'\d'
    DIGITS = '%s+' % DIGIT

    NUMBER = r'\d*[.]?\d+'
    MIXED_NUMBER = r'[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*'

    LETTER = '[a-zA-Z]'
    LETTERS = '%s+' % LETTER

    ALPHABET_NUMERIC = '[a-zA-Z0-9]'

    PUNCT = r'[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    PUNCTS = '%s+' % PUNCT
    PUNCTS_OR_PHRASE = '%s( %s)*' % (PUNCTS, PUNCTS)
    PUNCTS_OR_GROUP = '%s( +%s)*' % (PUNCTS, PUNCTS)
    PUNCTS_PHRASE = '%s( %s)+' % (PUNCTS, PUNCTS)
    PUNCTS_GROUP = '%s( +%s)+' % (PUNCTS, PUNCTS)
    CHECK_PUNCT = '%s$' % PUNCT
    CHECK_PUNCTS = '%s$' % PUNCTS
    CHECK_PUNCTS_GROUP = ' *%s *$' % PUNCTS_GROUP

    SPACE_PUNCT = r'[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]'
    MULTI_SPACE_PUNCTS = '%s+' % SPACE_PUNCT

    GRAPH = r'[\x21-\x7e]'

    WORD = r'[a-zA-Z][a-zA-Z0-9]*'
    WORDS = r'%s( %s)*' % (WORD, WORD)
    PHRASE = r'%s( %s)+' % (WORD, WORD)
    WORD_OR_GROUP = r'%s( +%s)*' % (WORD, WORD)
    WORD_GROUP = r'%s( +%s)+' % (WORD, WORD)

    MIXED_WORD = r'[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*'
    MIXED_WORDS = '%s( %s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_PHRASE = '%s( %s)+' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_OR_GROUP = '%s( +%s)*' % (MIXED_WORD, MIXED_WORD)
    MIXED_WORD_GROUP = '%s( +%s)+' % (MIXED_WORD, MIXED_WORD)

    NON_WHITESPACE = r'\S'
    NON_WHITESPACES = r'%s+' % NON_WHITESPACE
    NON_WHITESPACES_OR_PHRASE = r'%s( %s)*' % (NON_WHITESPACES, NON_WHITESPACES)
    NON_WHITESPACES_PHRASE = r'%s( %s)+' % (NON_WHITESPACES, NON_WHITESPACES)
    NON_WHITESPACES_OR_GROUP = r'%s( +%s)*' % (NON_WHITESPACES, NON_WHITESPACES)
    NON_WHITESPACES_GROUP = r'%s( +%s)+' % (NON_WHITESPACES, NON_WHITESPACES)


def get_ref_pattern_by_name(name, default=None):
    """Retrieve a regex pattern constant by name."""
    default = default or PATTERN.NON_WHITESPACES_OR_GROUP
    attr = name.upper()
    pattern = getattr(PATTERN, attr, default)
    return pattern
