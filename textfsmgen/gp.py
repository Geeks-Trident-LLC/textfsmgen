"""
textfsmgen.gp
=============

Grammar and parsing utilities for the TextFSM Generator.

This module provides helper functions, classes, and constants used to
interpret user-defined template snippets into normalized TextFSM grammar.
It acts as the parsing backbone of the TextFSM Generator, ensuring that
raw user input (lines, flags, operators, metadata) is consistently
translated into valid template statements.

Purpose
-------
- Define grammar rules and parsing logic for TextFSM templates.
- Normalize user input into canonical TextFSM syntax.
- Support advanced options such as flags, operators, and metadata.
- Provide reusable parsing utilities for other core modules.

Contents
--------
- Grammar definitions for template statements.
- Parsing functions for variables, operators, and flags.
- Utilities for handling metadata options (Filldown, Fillup, Key, List, Required).
- Error classes for invalid grammar or parsing failures.

Usage
-----
This module is typically used internally by higher-level components
such as `textfsmgen.core.TemplateBuilder` and `textfsmgen.main`.
Direct usage is uncommon, but developers may import it when extending
or debugging grammar rules.

Notes
-----
- All parsing functions return normalized TextFSM statements or raise
  a `TemplateParsedLineError` if input is invalid.
- This module is designed for internal use; external callers should
  prefer the `TemplateBuilder` interface.
"""

import re

from genericlib import NUMBER
from genericlib import STRING
from genericlib import PATTERN
from genericlib import TEXT
from genericlib import SYMBOL

from genericlib import Misc

from textfsmgen.exceptions import RuntimeException


class LData(RuntimeException):
    """
    Line number wrapper for string input with utilities to
    inspect leading and trailing whitespace.

    This class normalizes input by storing both the raw string
    and a stripped version. It provides properties to query
    leading/trailing whitespace and boolean flags to indicate
    their presence.

    Parameters
    ----------
    data : Any
        Input number to be wrapped. Converted to string internally.

    Attributes
    ----------
    raw_data : str
        Original string representation of the input.
    data : str
        Stripped version of `raw_data` with leading/trailing
        whitespace removed.
    """
    def __init__(self, data):
        self.raw_data = str(data)
        self.data = self.raw_data.strip()

    def __call__(self, *args, **kwargs):
        """
        Create a new instance of `LData` when the object is called.

        Returns
        -------
        LData
            A new line number instance initialized with the provided arguments.
        """
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def leading(self):
        """
        Extract leading whitespace from the raw number.

        Returns
        -------
        str
            Leading whitespace characters, or an empty string if none.
        """
        leading_spaces = Misc.get_leading_line(self.raw_data)
        return leading_spaces

    @property
    def trailing(self):
        """
        Extract trailing whitespace from the raw number.

        Returns
        -------
        str
            Trailing whitespace characters, or an empty string if none.
        """
        trailing_spaces = Misc.get_trailing_line(self.raw_data)
        return trailing_spaces

    @property
    def is_leading(self):
        """
        Check if the raw number contains leading whitespace.

        Returns
        -------
        bool
            True if leading whitespace exists, False otherwise.
        """
        chk = self.leading != STRING.EMPTY
        return chk

    @property
    def is_trailing(self):
        """
        Check if the raw number contains trailing whitespace.

        Returns
        -------
        bool
            True if trailing whitespace exists, False otherwise.
        """
        chk = self.trailing != STRING.EMPTY
        return chk


class TranslatedPattern(RuntimeException):
    """
    Represents a translated text pattern used in FSM (Finite State Machine)
    generation, providing utilities to normalize, store, and manipulate
    regex-compatible string patterns.

    The `TranslatedPattern` class is designed to wrap raw text input and
    convert it into a structured, regex-ready representation. It supports
    translation of text into pattern segments, validation of pattern syntax,
    and convenient access to both the original and processed forms.

    Notes
    -----
    - This class is primarily used internally by the `textfsmgen.gp` module
      to generate and validate regex patterns for parsing text.
    - Invalid patterns raise `TextPatternError`.
    """
    def __init__(self, data, *other, name='',
                 defined_pattern='', defined_patterns=None, ref_names=None,
                 singular_name='', singular_pattern='', root_name=''):
        self.data = str(data)
        self.lst_of_other_data = list(other)
        self.lst_of_all_data = [self.data] + self.lst_of_other_data
        self.defined_pattern = str(defined_pattern)
        self.defined_patterns = defined_patterns if isinstance(defined_patterns, list) else []
        self.ref_names = ref_names if isinstance(ref_names, (list, tuple)) else []
        self.singular_name = singular_name
        self.singular_pattern = singular_pattern
        self.root_name = root_name
        self.name = str(name)
        self._pattern = STRING.EMPTY
        self.process()

    def __len__(self):
        """
        Determine whether the pattern is non-empty.

        This method overrides `__len__` to return a boolean value
        instead of the usual integer length. It checks whether the
        internal `_pattern` string is empty.

        Returns
        -------
        bool
            True if `_pattern` is not empty, False if it equals
            `STRING.EMPTY`.
        """
        chk = self._pattern != STRING.EMPTY
        return chk

    def __call__(self, *args, **kwargs):
        """
        Enable the object to be invoked as a callable, returning a new instance
        of the same class.

        This method allows the class instance to behave like a factory: when
        called, it constructs and returns a new instance of `self.__class__`
        initialized with the provided arguments.

        Parameters
        ----------
        *args : arguments
            Positional arguments forwarded to the class constructor.
        **kwargs : keyword arguments
            Keyword arguments forwarded to the class constructor.

        Returns
        -------
        Self
            A new instance of the same class, initialized with the given
            arguments.
        """
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def translated(self):
        """
        Indicate whether the pattern has been translated into a non-empty value.

        Returns
        -------
        bool
            True if `_pattern` is non-empty (translation exists),
            False if `_pattern` equals `STRING.EMPTY`.
        """
        chk = self._pattern != STRING.EMPTY
        return chk

    @property
    def actual_name(self):
        """
        Resolve the effective name of the current pattern.

        This property attempts to map the internal `_pattern` to a
        corresponding reference name if both `defined_patterns` and
        `ref_names` are available. If no mapping exists, it falls
        back to the instance's `name` attribute.

        Returns
        -------
        str
            The resolved name of the pattern. Either:
            - The reference name associated with `_pattern`, or
            - The fallback `name` attribute if no mapping is found.
        """
        if self.defined_patterns and self.ref_names:
            idx = self.defined_patterns.index(self._pattern)
            return self.ref_names[idx]
        else:
            return self.name

    @property
    def lessen_name(self):
        """
        Resolve a simplified (lessened) name for the current pattern.

        This property maps certain reference names into broader, normalized
        categories to reduce redundancy. If both `defined_patterns` and
        `ref_names` are available, it attempts to locate the current `_pattern`
        in `defined_patterns` and retrieve the corresponding reference name.
        That name is then mapped to a simplified category using a lookup table.
        If no mapping exists, or if the pattern cannot be resolved, the
        instance's `name` attribute is returned.

        Returns
        -------
        str
            The simplified name of the pattern. Either:
            - A normalized category from the lookup table, or
            - The fallback `name` attribute if no mapping is found.

        Notes
        -----
        - Assumes `defined_patterns` and `ref_names` are aligned lists.
        - The lookup table groups related names into categories such as
          "puncts_or_group", "word_or_group", "mixed_word_or_group",
          and "non_whitespaces_or_group".
        """
        if self.defined_patterns and self.ref_names:
            idx = self.defined_patterns.index(self._pattern)
            name = self.ref_names[idx]

            tbl = dict(
                # punctuation-related groups
                puncts_or_group="puncts_or_group",
                puncts_group="puncts_or_group",
                puncts_phrase="puncts_or_group",
                puncts_or_phrase="puncts_or_group",

                # word-related groups
                word_or_group="word_or_group",
                word_group="word_or_group",
                phrase="word_or_group",
                words="word_or_group",

                # mixed word groups
                mixed_word_or_group="mixed_word_or_group",
                mixed_words="mixed_word_or_group",
                mixed_phrase="mixed_word_or_group",
                mixed_word_group="mixed_word_or_group",

                # non-whitespace groups
                non_whitespaces_or_group="non_whitespaces_or_group",
                non_whitespaces_or_phrase="non_whitespaces_or_group",
                non_whitespaces_phrase="non_whitespaces_or_group",
                non_whitespaces_group="non_whitespaces_or_group",
            )
            lessen_name = tbl.get(name, self.name)
            return lessen_name
        else:
            return self.name

    @property
    def pattern(self):
        """
        Access the underlying regex pattern string.

        This property provides read-only access to the internal `_pattern`
        attribute, which represents the current regex pattern associated
        with the instance.

        Returns
        -------
        str
            The raw regex pattern string stored in `_pattern`.
        """
        return self._pattern

    @property
    def lessen_pattern(self):
        """
        Resolve a simplified (lessened) pattern for the current instance.

        This property attempts to map the current `_pattern` into a broader,
        normalized category using `lessen_name`. If both `defined_patterns`
        and `ref_names` are available, it looks up the index of `lessen_name`
        in `ref_names` and returns the corresponding entry from
        `defined_patterns`. If no mapping exists, or if the lists are missing,
        the raw `pattern` is returned as a fallback.

        Returns
        -------
        str
            The simplified regex pattern string. Either:
            - A normalized pattern from `defined_patterns`, or
            - The fallback `pattern` attribute if no mapping is found.

        Notes
        -----
        - Assumes `defined_patterns` and `ref_names` are aligned lists.
        - Falls back gracefully if `lessen_name` is not present in `ref_names`.
        """
        if self.defined_patterns and self.ref_names:
            lessen_name = self.lessen_name
            idx = self.ref_names.index(lessen_name)
            lessen_pat = self.defined_patterns[idx]
            return lessen_pat
        else:
            return self.pattern

    @property
    def root_pattern(self):
        tbl = dict(
            non_whitespace=PATTERN.NON_WHITESPACE,
            non_whitespaces=PATTERN.NON_WHITESPACES,
            non_whitespaces_or_group=PATTERN.NON_WHITESPACES_OR_GROUP
        )
        root_pattern = tbl.get(self.root_name, PATTERN.NON_WHITESPACES_OR_GROUP)
        return root_pattern

    def process(self):
        """
        Resolve and assign the active regex pattern for the instance.

        This method attempts to match the current input against a set of
        defined patterns. If `defined_patterns` is available, it iterates
        through them to find the first match:

        - If `is_plural()` is True, only the last two patterns are checked.
        - Otherwise, all patterns in `defined_patterns` are considered.
        - On the first successful match, `_pattern` is set to that pattern.
        - If no match is found, `_pattern` is set to `STRING.EMPTY`.

        If `defined_patterns` is not available, the method falls back to
        checking `defined_pattern` directly.

        Returns
        -------
        None
            Updates the internal `_pattern` attribute in place.

        Notes
        -----
        - Relies on `check_matching(pat)` to determine whether a pattern
          matches the current input.
        - Ensures `_pattern` always resolves to either a valid pattern or
          `STRING.EMPTY`.
        """
        if self.defined_patterns:
            indices = slice(-2, None) if self.is_plural() else slice(None, None)
            defined_patterns = self.defined_patterns[indices]
            for pat in defined_patterns:
                if self.check_matching(pat):
                    self._pattern = pat
                    break
            else:
                self._pattern = STRING.EMPTY
        else:
            is_matched = self.check_matching(self.defined_pattern)
            self._pattern = self.defined_pattern if is_matched else STRING.EMPTY

    def check_matching(self, pattern):
        """
        Check whether all number entries match the given regex pattern.

        This method appends a trailing `$` to the provided pattern to ensure
        matches occur at the end of each string. It then evaluates every entry
        in `lst_of_all_data` using `re.match`. The result is True only if all
        entries match the pattern.

        Parameters
        ----------
        pattern : str
            The regex pattern to test against each number entry. A trailing `$`
            is automatically appended to enforce end-of-string matching.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` match the pattern,
            False otherwise.
        """
        pat = f"{pattern}$"
        is_matched = all(re.match(pat, data) for data in self.lst_of_all_data)
        return is_matched

    def is_digit(self) -> bool:
        """
        Check whether the current name corresponds to a digit pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.DIGIT` to determine if it represents a
        digit-based pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.DIGIT`, False otherwise.
        """
        return self.name == TEXT.DIGIT

    def is_digits(self) -> bool:
        """
        Check whether the current name corresponds to a digits pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.DIGITS` to determine if it represents a
        multi-digit pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.DIGITS`, False otherwise.
        """
        return self.name == TEXT.DIGITS

    def is_number(self) -> bool:
        """
        Check whether the current name corresponds to a number pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.NUMBER` to determine if it represents a
        numeric pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.NUMBER`, False otherwise.
        """
        return self.name == TEXT.NUMBER

    def is_mixed_number(self) -> bool:
        """
        Check whether the current name corresponds to a mixed number pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.MIXED_NUMBER` to determine if it represents
        a mixed numeric pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.MIXED_NUMBER`, False otherwise.
        """
        return self.name == TEXT.MIXED_NUMBER

    def is_letter(self) -> bool:
        """
        Check whether the current name corresponds to a letter pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.LETTER` to determine if it represents a
        single letter pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.LETTER`, False otherwise.
        """
        return self.name == TEXT.LETTER

    def is_letters(self) -> bool:
        """
        Check whether the current name corresponds to a letters pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.LETTERS` to determine if it represents a
        multiple-letters pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.LETTERS`, False otherwise.
        """
        return self.name == TEXT.LETTERS

    def is_alphabet_numeric(self) -> bool:
        """
        Check whether the current name corresponds to an alphanumeric pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.ALPHABET_NUMERIC` to determine if it represents
        a pattern consisting of both alphabetic and numeric characters.

        Returns
        -------
        bool
            True if `name` equals `TEXT.ALPHABET_NUMERIC`, False otherwise.
        """
        return self.name == TEXT.ALPHABET_NUMERIC

    def is_symbol(self) -> bool:
        """
        Check whether the current name corresponds to a symbol pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.PUNCT` to determine if it represents a
        punctuation or symbol pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.PUNCT`, False otherwise.
        """
        return self.name == TEXT.PUNCT

    def is_symbols(self) -> bool:
        """
        Check whether the current name corresponds to a symbols pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.PUNCTS` to determine if it represents a
        multiple-symbols pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.PUNCTS`, False otherwise.
        """
        return self.name == TEXT.PUNCTS

    def is_symbols_group(self) -> bool:
        """
        Check whether the current name corresponds to a symbols group pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.PUNCTS_GROUP` to determine if it represents
        a grouped symbols pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.PUNCTS_GROUP`, False otherwise.
        """
        return self.name == TEXT.PUNCTS_GROUP

    def is_graph(self) -> bool:
        """
        Check whether the current name corresponds to a graph pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.GRAPH` to determine if it represents a
        graph-related pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.GRAPH`, False otherwise.
        """
        return self.name == TEXT.GRAPH

    def is_word(self) -> bool:
        """
        Check whether the current name corresponds to a word pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.WORD` to determine if it represents a
        single word pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.WORD`, False otherwise.
        """
        return self.name == TEXT.WORD

    def is_words(self) -> bool:
        """
        Check whether the current name corresponds to a words pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.WORDS` to determine if it represents a
        multiple-words pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.WORDS`, False otherwise.
        """
        return self.name == TEXT.WORDS

    def is_mixed_word(self) -> bool:
        """
        Check whether the current name corresponds to a mixed word pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.MIXED_WORD` to determine if it represents
        a mixed word pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.MIXED_WORD`, False otherwise.
        """
        return self.name == TEXT.MIXED_WORD

    def is_mixed_words(self) -> bool:
        """
        Check whether the current name corresponds to a mixed words pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.MIXED_WORDS` to determine if it represents
        a multiple mixed-words pattern.

        Returns
        -------
        bool
            True if `name` equals `TEXT.MIXED_WORDS`, False otherwise.
        """
        return self.name == TEXT.MIXED_WORDS

    def is_non_whitespace(self) -> bool:
        """
        Check whether the current name corresponds to a non-whitespace pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.NON_WHITESPACE` to determine if it represents
        a pattern that excludes whitespace characters.

        Returns
        -------
        bool
            True if `name` equals `TEXT.NON_WHITESPACE`, False otherwise.
        """
        return self.name == TEXT.NON_WHITESPACE

    def is_non_whitespaces(self) -> bool:
        """
        Check whether the current name corresponds to a non-whitespaces pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.NON_WHITESPACES` to determine if it represents
        a pattern that excludes multiple whitespace characters.

        Returns
        -------
        bool
            True if `name` equals `TEXT.NON_WHITESPACES`, False otherwise.
        """
        return self.name == TEXT.NON_WHITESPACES

    def is_non_whitespaces_group(self) -> bool:
        """
        Check whether the current name corresponds to a non-whitespaces group pattern.

        This method compares the instance's `name` attribute against
        the constant `TEXT.NON_WHITESPACES_GROUP` to determine if it
        represents a grouped pattern that excludes whitespace characters.

        Returns
        -------
        bool
            True if `name` equals `TEXT.NON_WHITESPACES_GROUP`, False otherwise.
        """
        return self.name == TEXT.NON_WHITESPACES_GROUP

    def is_group(self):
        """
        Check whether the current name corresponds to any defined group pattern.

        This method evaluates multiple boolean helpers to determine if the
        instance represents a grouped pattern. It returns True if the name
        matches symbols group, words, mixed words, or non-whitespaces group.

        Returns
        -------
        bool
            True if the instance corresponds to any group pattern, False otherwise.
        """
        chk = (
                self.is_symbols_group()
                or self.is_words()
                or self.is_mixed_words()
                or self.is_non_whitespaces_group()
        )
        return chk

    def is_group_with_multi_spaces(self) -> bool:
        """
        Check whether the current group contains entries with multiple consecutive spaces.

        This method first verifies that the instance corresponds to a valid group
        using `is_group()`. If so, it iterates through all number entries in
        `lst_of_all_data` and checks whether any entry, after stripping leading
        and trailing whitespace, contains the constant `STRING.DOUBLE_SPACES`.

        Returns
        -------
        bool
            True if the group contains at least one entry with multiple spaces,
            False otherwise.
        """
        if not self.is_group():
            return False

        return any(STRING.DOUBLE_SPACES in data.strip() for data in
                   self.lst_of_all_data)

    def is_numeric(self) -> bool:
        """
        Check whether all entries in the number list are numeric.

        This method iterates through each entry in `lst_of_all_data`
        and verifies that every entry consists only of numeric characters
        using the built-in `str.isnumeric()` method.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` are numeric,
            False otherwise.
        """
        return all(data.isnumeric() for data in self.lst_of_all_data)

    def is_alphabet(self) -> bool:
        """
        Check whether all entries in the number list are alphabetic.

        This method iterates through each entry in `lst_of_all_data`
        and verifies that every entry consists only of alphabetic
        characters using the built-in `str.isalpha()` method.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` are alphabetic,
            False otherwise.
        """
        return all(data.isalpha() for data in self.lst_of_all_data)

    def is_not_alphabet(self) -> bool:
        """
        Check whether all entries in the number list are non-alphabetic.

        This method iterates through each entry in `lst_of_all_data`
        and verifies that every entry does not consist solely of
        alphabetic characters, using the built-in `str.isalpha()` method.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` are non-alphabetic,
            False otherwise.
        """
        return all(not data.isalpha() for data in self.lst_of_all_data)

    def is_punctuation(self) -> bool:
        """
        Check whether all entries in the number list are punctuation characters.

        This method iterates through each entry in `lst_of_all_data`
        and verifies that every entry is printable but not alphanumeric,
        which classifies it as punctuation.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` are punctuation,
            False otherwise.
        """
        return all(data.isprintable() and not data.isalnum() for data in
                   self.lst_of_all_data)

    def is_printable(self) -> bool:
        """
        Check whether all entries in the number list are printable.

        This method iterates through each entry in `lst_of_all_data`
        and verifies that every entry consists only of printable
        characters using the built-in `str.isprintable()` method.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` are printable,
            False otherwise.
        """
        return all(data.isprintable() for data in self.lst_of_all_data)

    def is_subset_of(self, other) -> bool:
        """
        Verify whether the current instance is a subset of another.

        This method is a placeholder for subset verification logic.
        It raises a NotImplementedError to indicate that the functionality
        has not yet been implemented. The error message includes the
        class names of both the current instance and the provided `other`
        object for clarity.

        Parameters
        ----------
        other : instance of TranslatedPattern or inherited of TranslatedPattern
            The object to compare against for subset verification.

        Raises
        ------
        NotImplementedError
            Always raised to indicate that subset verification
            is not yet implemented.
        """
        cls_name = Misc.get_instance_class_name(self)
        other_cls_name = Misc.get_instance_class_name(other)
        error = f"Subset verification not implemented for ({cls_name}, {other_cls_name})"
        raise NotImplementedError(error)

    def is_superset_of(self, other) -> bool:
        """
        Verify whether the current instance is a superset of another.

        This method is a placeholder for superset verification logic.
        It raises a NotImplementedError to indicate that the functionality
        has not yet been implemented. The error message includes the
        class names of both the current instance and the provided `other`
        object for clarity.

        Parameters
        ----------
        other : instance of TranslatedPattern or inherited of TranslatedPattern
            The object to compare against for superset verification.

        Raises
        ------
        NotImplementedError
            Always raised to indicate that superset verification
            is not yet implemented.
        """
        cls_name = Misc.get_instance_class_name(self)
        other_cls_name = Misc.get_instance_class_name(other)
        error = f"Superset verification not implemented for ({cls_name}, {other_cls_name})"
        raise NotImplementedError(error)

    def get_new_subset(self, other):
        """
        Create a new translated pattern instance representing a subset of another object.

        Parameters
        ----------
        other : TranslatedPattern
            An instance of `TranslatedPattern` or its subclass against which
            this pattern is considered a subset.

        Returns
        -------
        TranslatedPattern
            A new instance of `other` representing the subset relationship.
        """
        new_instance = other(other.data, other.get_reference_data(self))
        return new_instance

    def get_new_superset(self, other):
        """
        Create a new translated pattern instance representing a superset of another object.

        Parameters
        ----------
        other : TranslatedPattern
            An instance of `TranslatedPattern` or its subclass against which
            this pattern is considered a superset.

        Returns
        -------
        TranslatedPattern
            A new instance of `self` representing the superset relationship.
        """
        new_instance = self(self.data, self.get_reference_data(other))
        return new_instance

    def is_plural(self) -> bool:
        """
        Check whether all entries in the number list contain multiple words.

        This method iterates through each entry in `lst_of_all_data`,
        strips leading and trailing whitespace, splits the entry by
        the whitespace pattern defined in `PATTERN.WHITESPACES`, and
        verifies that the resulting list has more than one element.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` contain more than
            one word, False otherwise.
        """
        return all(
            len(re.split(PATTERN.WHITESPACES, data.strip())) > NUMBER.ONE
            for data in self.lst_of_all_data
        )

    def is_singular(self) -> bool:
        """
        Check whether all entries in the number list contain a single word.

        This method iterates through each entry in `lst_of_all_data`,
        strips leading and trailing whitespace, splits the entry by
        the whitespace pattern defined in `PATTERN.WHITESPACES`, and
        verifies that the resulting list has at most one element.

        Returns
        -------
        bool
            True if all entries in `lst_of_all_data` contain one word
            or none, False otherwise.
        """
        return all(
            len(re.split(PATTERN.WHITESPACES, data.strip())) <= NUMBER.ONE
            for data in self.lst_of_all_data
        )

    def is_mixing_singular_plural(self) -> bool:
        """
        Check whether the number list mixes singular and plural entries.

        This method evaluates the contents of `lst_of_all_data` by
        leveraging `is_singular()` and `is_plural()`. It returns True
        if the entries are neither entirely singular nor entirely plural,
        indicating a mixture of both forms.

        Returns
        -------
        bool
            True if the number list contains a mix of singular and plural
            entries, False otherwise.
        """
        return not self.is_singular() and not self.is_plural()

    def get_singular_data(self) -> str:
        """
        Extract the first word from the number string.

        This method splits the `number` attribute by the space character
        defined in `STRING.SPACE_CHAR` and returns the first element
        of the resulting list.

        Returns
        -------
        str
            The first word from `number`.
        """
        return self.data.split(STRING.SPACE_CHAR)[NUMBER.ZERO]

    def get_plural_data(self) -> str:
        """
        Retrieve plural number from the list of entries.

        This method iterates through each entry in `lst_of_all_data`,
        strips leading and trailing whitespace, and checks for the
        presence of a space character defined in `STRING.SPACE_CHAR`.
        If such an entry is found, it is returned. Otherwise, a new
        plural string is constructed by duplicating `self.number`
        separated by a space.

        Returns
        -------
        str
            An entry containing a space if found in `lst_of_all_data`,
            otherwise a constructed plural string from `self.number`.
        """
        for data in self.lst_of_all_data:
            if STRING.SPACE_CHAR in data.strip():
                return data
        return f"{self.data} {self.data}"

    def get_reference_data(self, other):
        """
        Retrieve reference number based on the relationship with another object.

        This method determines the appropriate reference number by checking
        the type and relationship of `other` relative to the current instance.

        Logic
        -----
        - If `other` is an instance of `TranslatedPattern`:
            * If `self` is a subset or superset of `other`, return `other.number`.
            * If both `self` and `other` are plural, return `self.number`.
            * Otherwise, return the singular form of `self.number` via
              `get_singular_data()`.
        - If `other` is not a `TranslatedPattern`, return `self.number`.

        Parameters
        ----------
        other : instance of TranslatedPattern or inherited of TranslatedPattern
            The object to compare against. It is an instance of
            `TranslatedPattern` or another type.

        Returns
        -------
        str
            The selected reference number string based on the relationship
            between `self` and `other`.
        """
        if isinstance(other, TranslatedPattern):
            if self.is_subset_of(other) or self.is_superset_of(other):
                return other.data
            if self.is_plural() and other.is_plural():
                return self.data
            return self.get_singular_data()
        return self.data

    def raise_recommend_exception(self, other) -> None:
        """
        Raise a runtime exception for unimplemented recommended pattern cases.

        This method constructs a descriptive error message indicating that
        handling for the given `(self, other)` case is not yet implemented.
        The message includes the number attributes of both objects and the
        class name of `self`. It then raises a runtime exception using
        `raise_runtime_error`.

        Parameters
        ----------
        other : instance of TranslatedPattern or inherited of TranslatedPattern
            The object involved in the unimplemented case. Must provide
            a `number` attribute for inclusion in the error message.

        Raises
        ------
        Exception
            A dynamically created runtime exception with the name
            "NotImplementRecommendedRTPattern" and a descriptive message.
        """
        cls_name = Misc.get_instance_class_name(self)

        if isinstance(other, TranslatedPattern):
            other_repr = repr(other.data)
        else:
            other_repr = f"<Unknown:instance of {type(other).__name__}>"

        msg = (
            f"Recommended pattern not implemented for class {cls_name} "
            f"with number pair ({self.data!r}, {other_repr})"
        )

        self.raise_runtime_error(
            name="NotImplementRecommendedRTPattern",
            msg=msg,
        )

    def get_readable_snippet(self, var: str = "") -> str:
        """
        Generate a human-readable snippet representation of the pattern.

        This method constructs a formatted string representation of the
        current pattern. It ensures that the instance has a valid `name`,
        replaces parentheses in `number` with symbolic placeholders, and
        then builds a snippet string. If a variable name is provided, it
        is included in the snippet; otherwise, only the value is shown.

        Parameters
        ----------
        var : str, optional
            An optional variable name to include in the snippet. Defaults
            to an empty string.

        Returns
        -------
        str
            A formatted snippet string containing the pattern's name,
            optional variable, and value.

        Raises
        ------
        RuntimeError
            If `name` is not defined, a runtime error is raised with
            the identifier "TranslatedPatternSnippetRTError".
        """
        if not self.name:
            self.raise_runtime_error(
                name="TranslatedPatternSnippetRTError",
                msg="Cannot create snippet without a defined name",
            )

        value = self.data.replace(SYMBOL.LEFT_PARENTHESIS, "_SYMBOL_LEFT_PARENTHESIS_")
        value = value.replace(SYMBOL.RIGHT_PARENTHESIS,"_SYMBOL_RIGHT_PARENTHESIS_")

        if var:
            return f"{self.actual_name}(var={var}, value={value})"
        return f"{self.actual_name}(value={value})"

    def get_regex_pattern(self, var: str = "", is_lessen: bool = False,
                          is_root: bool = False) -> str:
        """
        Generate a regex pattern string for the current instance.

        This method constructs a regex pattern based on the instance's
        attributes and optional flags. It ensures that the instance has
        a valid `name` before proceeding. Depending on the flags, the
        pattern may be derived from `lessen_pattern` or `root_pattern`.
        If a variable name is provided, the pattern is wrapped in a
        named capturing group.

        Parameters
        ----------
        var : str, optional
            An optional variable name to wrap the pattern in a named
            capturing group. Defaults to an empty string.
        is_lessen : bool, optional
            If True, use `lessen_pattern` instead of `pattern`.
            Defaults to False.
        is_root : bool, optional
            If True, use `root_pattern` instead of `pattern`.
            Defaults to False.

        Returns
        -------
        str
            The constructed regex pattern string.

        Raises
        ------
        RuntimeError
            If `name` is not defined, a runtime error is raised with
            the identifier "TranslatedPatternRegexRTError".
        """
        if not self.name:
            self.raise_runtime_error(
                name="TranslatedPatternRegexRTError",
                msg="Cannot create regex pattern without a defined name",
            )

        pattern = self.lessen_pattern if is_lessen else self.pattern
        pattern = self.root_pattern if is_root else pattern

        if var:
            pattern = f"(?P<{var}>{pattern})"

        return pattern

    def get_template_snippet(self, var: str = "", is_lessen: bool = False,
                             is_root: bool = False) -> str:
        """
        Generate a template snippet string for the current pattern.

        This method constructs a formatted template snippet based on the
        instance's attributes and optional flags. It ensures that the
        instance has a valid `name` before proceeding. Depending on the
        flags, the snippet may use `lessen_name` or `root_name`. If a
        variable name is provided, it is prefixed with `"var_"` and
        included in the snippet.

        Parameters
        ----------
        var : str, optional
            An optional variable name to include in the snippet. If provided,
            it is prefixed with `"var_"`. Defaults to an empty string.
        is_lessen : bool, optional
            If True, use `lessen_name` instead of `actual_name`. Defaults to False.
        is_root : bool, optional
            If True, use `root_name` instead of `actual_name`. Defaults to False.

        Returns
        -------
        str
            A formatted template snippet string containing the pattern's name
            and optional variable.

        Raises
        ------
        RuntimeError
            If `name` is not defined, a runtime error is raised with the
            identifier "TranslatedPatternTemplateSnippetRTError".
        """
        if not self.name:
            self.raise_runtime_error(
                name="TranslatedPatternTemplateSnippetRTError",
                msg="Cannot create template snippet without a defined name",
            )

        var_txt = f"var_{var}" if var else STRING.EMPTY
        name = self.lessen_name if is_lessen else self.actual_name
        name = self.root_name if is_root else name

        return f"{name}({var_txt})"

    @classmethod
    def do_factory_create(cls, data: str, *other):
        """
        Factory method to create a translated pattern instance.

        This method attempts to construct an instance of one of several
        `TranslatedPattern` subclasses using the provided `number` and
        optional arguments. It iterates through a predefined list of
        candidate classes and returns the first successfully created
        instance. If no suitable class can handle the input, a runtime
        error is raised.

        Parameters
        ----------
        data : str
            The primary input number used to initialize the pattern.
        *other : other arguments
            Additional arguments passed to the candidate class constructors.

        Returns
        -------
        None or instance of TranslatedPattern or inherited of TranslatedPattern
            An instance of the first matching subclass that successfully
            handles the input number.

        Raises
        ------
        RuntimeError
            If no subclass can handle the given input, a runtime error
            is raised with the identifier "FactoryTranslatedPatternRTIssue".
        """
        classes = [
            TranslatedDigitPattern,
            TranslatedDigitsPattern,

            TranslatedNumberPattern,

            TranslatedLetterPattern,
            TranslatedLettersPattern,

            TranslatedAlphabetNumericPattern,
            TranslatedWordPattern,

            TranslatedPunctPattern,
            TranslatedPunctsPattern,
            TranslatedPunctsGroupPattern,

            TranslatedGraphPattern,

            TranslatedMixedNumberPattern,
            TranslatedMixedWordPattern,

            TranslatedWordsPattern,

            TranslatedMixedWordsPattern,

            TranslatedNonWhitespacePattern,
            TranslatedNonWhitespacesPattern,
            TranslatedNonWhitespacesGroupPattern,
        ]
        for class_ in classes:
            node = class_(data, *other)
            if node:
                return node
        RuntimeException.do_raise_runtime_error(    # noqa
            obj="FactoryTranslatedPatternRTIssue",
            msg=f"Factory could not create a pattern for number={data!r}, other={other!r}",
        )

    @classmethod
    def recommend_pattern(cls, translated_pat_obj1, translated_pat_obj2):
        """
        Recommend a generalized pattern from two translated pattern objects.

        This factory-style method delegates to the `recommend` method of
        `translated_pat_obj1`, passing `translated_pat_obj2` as the argument.
        It returns the generalized pattern produced by the recommendation
        logic defined in the first object.

        Parameters
        ----------
        translated_pat_obj1 : Instance of TranslatedPattern or inherited of TranslatedPattern
            The primary translated pattern object. Must implement a
            `recommend` method.
        translated_pat_obj2 : Instance of TranslatedPattern or inherited of TranslatedPattern
            The secondary translated pattern object to be compared against.

        Returns
        -------
        Instance of TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance recommended based
            on the relationship between the two input objects.
        """
        generalized_pat = translated_pat_obj1.recommend(translated_pat_obj2)
        return generalized_pat

    @classmethod
    def recommend_pattern_using_data(cls, data1: str, data2: str):
        """
        Recommend a generalized pattern from two raw number inputs.

        This factory-style method first creates translated pattern
        objects from the provided input number using `do_factory_create`.
        It then delegates to the `recommend` method of the first
        translated pattern object, passing the second as the argument.
        The result is a generalized pattern instance based on the
        relationship between the two inputs.

        Parameters
        ----------
        data1 : str
            The first raw number input used to create a translated pattern.
        data2 : str
            The second raw number input used to create a translated pattern.

        Returns
        -------
        Instance of TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance recommended based
            on the relationship between the two input number values.
        """
        translated_pat_obj1 = cls.do_factory_create(data1)
        translated_pat_obj2 = cls.do_factory_create(data2)
        return translated_pat_obj1.recommend(translated_pat_obj2)


class TranslatedDigitPattern(TranslatedPattern):
    """
    A translated pattern class specialized for single-digit inputs.

    This class extends `TranslatedPattern` to handle digit-specific
    cases. It defines subset and superset relationships with other
    translated patterns and provides recommendation logic for
    generating generalized patterns when combined with other types.

    Parameters
    ----------
    data : str
        The primary input number representing a digit.
    *other : list of arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        The identifier for this pattern type (digit).
    defined_pattern : str
        The regex pattern used to match digits.
    root_name : str
        The root category name for this pattern ("non_whitespace").
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name=TEXT.DIGIT,
            defined_pattern=PATTERN.DIGIT,
            root_name="non_whitespace",
        )

    def is_subset_of(self, other):
        """
        Check if this digit pattern is a subset of another pattern.

        A digit is considered a subset of broader categories such as
        digits, numbers, mixed numbers, alphanumeric, graphs, words,
        mixed words, non-whitespace, and related groupings.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to compare against.

        Returns
        -------
        bool
            True if this digit pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`, a
            `NotImplementRecommendedRTPattern` exception is raised.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        chk = (
            other.is_digit()
            or other.is_digits()
            or other.is_number()
            or other.is_mixed_number()
            or other.is_alphabet_numeric()
            or other.is_graph()
            or other.is_word()
            or other.is_mixed_word()
            or other.is_words()
            or other.is_mixed_words()
            or other.is_non_whitespace()
            or other.is_non_whitespaces()
            or other.is_non_whitespaces_group()
        )
        return chk

    def is_superset_of(self, other):
        """
        Check if this digit pattern is a superset of another pattern.

        Digit is not considered supersets of any other pattern.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to compare against.

        Returns
        -------
        bool
            Always False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`, a
            `NotImplementRecommendedRTPattern` exception is raised.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return False

    def recommend(self, other):
        """
        Recommend a generalized pattern when combined with another pattern.

        This method determines how a digit pattern should be generalized
        when paired with another translated pattern. If the digit is a
        subset or superset of `other`, a new subset or superset pattern
        is returned. Otherwise, specific combinations with letters,
        symbols, or groups produce broader generalized patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this digit pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this digit and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other) or self.is_superset_of(other):
            return (
                self.get_new_subset(other)
                if self.is_subset_of(other)
                else self.get_new_superset(other)
            )

        if other.is_letter():
            return TranslatedAlphabetNumericPattern(self.data, other.data)
        if other.is_letters():
            return TranslatedWordPattern(self.data, other.data)
        if other.is_symbol():
            return TranslatedNonWhitespacePattern(self.data, other.data)
        if other.is_symbols():
            return TranslatedNonWhitespacesPattern(self.data, other.data)
        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedDigitsPattern(TranslatedPattern):
    """
    A translated pattern class specialized for multiple digit inputs.

    This class extends `TranslatedPattern` to handle digit-specific
    cases. It defines subset and superset relationships with other
    translated patterns and provides recommendation logic for
    generating generalized patterns when combined with other types.

    Parameters
    ----------
    data : str
        The primary input number representing digit(s).
    *other : list of arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        The identifier for this pattern type (digit).
    defined_pattern : str
        The regex pattern used to match digits.
    root_name : str
        The root category name for this pattern ("non_whitespace").
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name=TEXT.DIGITS,
            defined_pattern=PATTERN.DIGITS,
            root_name='non_whitespaces'
        )

    def is_subset_of(self, other):
        """
        Determine whether this digit pattern is a subset of another translated pattern.

        Digits-pattern is considered a subset of broader categories such as
        digits, numbers, mixed numbers, words, mixed words, non-whitespace
        sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against. Must be a subclass of
            `TranslatedPattern`. If not, a recommendation exception is raised.

        Returns
        -------
        bool
            True if this digit pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`, a
            `NotImplementRecommendedRTPattern` exception is raised.
        """

        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_word(),
            other.is_mixed_word(),
            other.is_words(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other):
        """
        Determine whether this digit pattern is a superset of another translated pattern.

        Digits-pattern is only considered a superset when the other pattern
        represents a single digit. For all other cases, this method returns False.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against. Must be a subclass of
            `TranslatedPattern`. If not, a recommendation exception is raised.

        Returns
        -------
        bool
            True if this digit pattern is a superset of `other` (i.e., when
            `other` is a digit), otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`, a
            `NotImplementRecommendedRTPattern` exception is raised.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_digit()

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        This method determines how digits-pattern should be generalized
        when paired with another translated pattern. If the digit is a
        subset or superset of `other`, a new subset or superset pattern
        is returned. Otherwise, specific combinations with letters,
        symbols, graphs, or non-whitespace categories produce broader
        generalized patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this digit pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this digit and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case,
            a `NotImplementRecommendedRTPattern` exception is raised.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letter(), other.is_letters(),
                other.is_alphabet_numeric()]):
            return TranslatedWordPattern(self.data, other.data)

        if any([other.is_symbol(), other.is_symbols(), other.is_graph()]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        if other.is_non_whitespace():
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedNumberPattern(TranslatedPattern):
    """
    Specialized translated pattern for numeric inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    numbers. It provides subset and superset checks against other
    translated patterns and supports recommendation logic for
    generalization when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a number.
    *other : list of arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("number").
    defined_pattern : str
        Regex pattern used to match numeric values.
    root_name : str
        Root category name for this pattern ("non_whitespaces").
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name=TEXT.NUMBER,
            defined_pattern=PATTERN.NUMBER,
            root_name='non_whitespaces'
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this number pattern is a subset of another translated pattern.

        A number is considered a subset of broader categories such as
        numbers, mixed numbers, mixed words, non-whitespace sequences,
        and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this number pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_number(),
            other.is_mixed_number(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this number pattern is a superset of another translated pattern.

        A number is considered a superset when the other pattern
        represents a digit or a sequence of digits.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this number pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_digit() or other.is_digits()

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this number pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with letters, words, symbols, graphs,
        or non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this number pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this number and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letter(), other.is_letters(),
                other.is_alphabet_numeric(), other.is_graph(), other.is_word()]):
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_words():
            return TranslatedMixedWordsPattern(self.data, other.data)

        if any([other.is_symbol(), other.is_symbols(), other.is_non_whitespace()]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedMixedNumberPattern(TranslatedPattern):
    """
    Specialized translated pattern for mixed numeric inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    mixed numbers (e.g., alphanumeric strings containing digits and
    letters). It provides subset and superset checks against other
    translated patterns and supports recommendation logic for
    generalization when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a mixed number.
    *other : list of arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("mixed_number").
    defined_pattern : str
        Regex pattern used to match mixed numeric values.
    root_name : str
        Root category name for this pattern ("non_whitespaces").
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name=TEXT.MIXED_NUMBER,
            defined_pattern=PATTERN.MIXED_NUMBER,
            root_name="non_whitespaces",
        )

    def is_subset_of(self, other):
        """
        Determine whether this mixed number pattern is a subset of another translated pattern.

        A mixed number is considered a subset of broader categories such as
        mixed numbers, mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this mixed number pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_mixed_number(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other):
        """
        Determine whether this mixed number pattern is a superset of another translated pattern.

        A mixed number is considered a superset when the other pattern
        represents a digit, a sequence of digits, or a number.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this mixed number pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this mixed number pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with letters, words, symbols, graphs,
        or non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this mixed number pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this mixed number and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letter(), other.is_letters(),
                other.is_alphabet_numeric(), other.is_graph(), other.is_word()]):
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_words():
            return TranslatedMixedWordsPattern(self.data, other.data)

        if any([other.is_symbol(), other.is_symbols(), other.is_non_whitespace()]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedLetterPattern(TranslatedPattern):
    """
    Specialized translated pattern for single-letter inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    letters. It provides subset and superset checks against other
    translated patterns and supports recommendation logic for
    generalization when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a letter.
    *other : list of arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("letter").
    defined_pattern : str
        Regex pattern used to match a single letter.
    root_name : str
        Root category name for this pattern ("non_whitespace").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.LETTER,
            defined_pattern=PATTERN.LETTER,
            root_name="non_whitespace",
        )

    def is_subset_of(self, other):
        """
        Determine whether this letter pattern is a subset of another translated pattern.

        A letter is considered a subset of broader categories such as
        letters, alphanumeric, graphs, words, mixed words, non-whitespace
        sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this letter pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other):
        """
        Determine whether this letter pattern is a superset of another translated pattern.

        A letter pattern is not considered a superset of any other
        translated pattern. This method always returns False.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            Always False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        return False

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this letter pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with digits, numbers, symbols, or
        non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this letter pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this letter and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_digit():
            return TranslatedAlphabetNumericPattern(self.data, other.data)
        if other.is_digits():
            return TranslatedWordPattern(self.data, other.data)
        if other.is_number() or other.is_mixed_number():
            return TranslatedMixedWordPattern(self.data, other.data)
        if other.is_symbol():
            return TranslatedGraphPattern(self.data, other.data)
        if other.is_symbols():
            return TranslatedNonWhitespacesPattern(self.data, other.data)
        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedLettersPattern(TranslatedPattern):
    """
    Specialized translated pattern for multi-letter inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    sequences of letters. It provides subset and superset checks against
    other translated patterns and supports recommendation logic for
    generalization when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing one or more letters.
    *other : list of other arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("letters").
    defined_pattern : str
        Regex pattern used to match sequences of letters.
    root_name : str
        Root category name for this pattern ("non_whitespaces").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.LETTERS,
            defined_pattern=PATTERN.LETTERS,
            root_name="non_whitespaces",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this letters pattern is a subset of another translated pattern.

        A sequence of letters is considered a subset of broader categories such as
        words, mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this letters pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letters(),
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this letters pattern is a superset of another translated pattern.

        A sequence of letters is considered a superset when the other pattern
        represents a single letter.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this letters pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_letter()

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this letters pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with digits, numbers, symbols, or
        non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this letters pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this letters pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_digit() or other.is_digits() or other.is_alphabet_numeric():
            return TranslatedWordPattern(self.data, other.data)

        if any([other.is_number(), other.is_mixed_number(), other.is_graph()]):
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        if any([other.is_symbol(), other.is_symbols(), other.is_non_whitespace()]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedAlphabetNumericPattern(TranslatedPattern):
    """
    Specialized translated pattern for alphanumeric inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    alphanumeric strings (letters combined with digits). It provides
    subset and superset checks against other translated patterns and
    supports recommendation logic for generalization when combined
    with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing an alphanumeric sequence.
    *other : list of other arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("alphabet_numeric").
    defined_pattern : str
        Regex pattern used to match alphanumeric values.
    root_name : str
        Root category name for this pattern ("non_whitespace").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.ALPHABET_NUMERIC,
            defined_pattern=PATTERN.ALPHABET_NUMERIC,
            root_name="non_whitespace",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this alphanumeric pattern is a subset of another translated pattern.

        An alphanumeric sequence is considered a subset of broader categories such as
        alphanumeric, words, mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this alphanumeric pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this alphanumeric pattern is a superset of another translated pattern.

        An alphanumeric sequence is considered a superset when the other pattern
        represents a letter, multiple letters, or a digit.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this alphanumeric pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_digit(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this alphanumeric pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with digits, numbers, symbols, or
        non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this alphanumeric pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this alphanumeric pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_digits():
            return TranslatedWordPattern(self.data, other.data)

        if other.is_number() or other.is_mixed_number():
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_symbol():
            return TranslatedNonWhitespacePattern(self.data, other.data)

        if other.is_symbols():
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedPunctPattern(TranslatedPattern):
    """
    Specialized translated pattern for punctuation characters.

    This subclass of `TranslatedPattern` defines behavior specific to
    punctuation marks. It provides subset and superset checks against
    other translated patterns and supports recommendation logic for
    generalization when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a punctuation character.
    *other : list of other arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("punct").
    defined_pattern : str
        Regex pattern used to match punctuation characters.
    root_name : str
        Root category name for this pattern ("non_whitespace").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.PUNCT,
            defined_pattern=PATTERN.PUNCT,
            root_name="non_whitespace",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this punctuation pattern is a subset of another translated pattern.

        A punctuation mark is considered a subset of broader categories such as
        symbols, graphs, mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this punctuation pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_symbol(),
            other.is_graph(),
            other.is_symbols(),
            other.is_symbols_group(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this punctuation pattern is a superset of another translated pattern.

        A punctuation mark is not considered a superset of any other
        translated pattern. This method always returns False.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            Always False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        return False

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this punctuation pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with letters, digits, numbers, or words
        produce broader generalized patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this punctuation pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this punctuation pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letter(), other.is_digit(), other.is_alphabet_numeric()]):
            return TranslatedGraphPattern(self.data)

        if any([other.is_letters(), other.is_digits(),
                other.is_number(), other.is_mixed_number(), other.is_word()]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_words():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedPunctsPattern(TranslatedPattern):
    """
    Specialized translated pattern for multiple punctuation characters.

    This subclass of `TranslatedPattern` defines behavior specific to
    sequences of punctuation marks. It provides subset and superset
    checks against other translated patterns and supports recommendation
    logic for generalization when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing one or more punctuation characters.
    *other : tuple, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("puncts").
    defined_pattern : str
        Regex pattern used to match sequences of punctuation characters.
    root_name : str
        Root category name for this pattern ("non_whitespaces").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.PUNCTS,
            defined_pattern=PATTERN.PUNCTS,
            root_name="non_whitespaces",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this punctuation sequence is a subset of another translated pattern.

        A sequence of punctuation marks is considered a subset of broader categories such as
        symbols, mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this punctuation sequence is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_symbols(),
            other.is_symbols_group(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this punctuation sequence is a superset of another translated pattern.

        A sequence of punctuation marks is considered a superset when the other pattern
        represents a single symbol.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this punctuation sequence is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_symbol()

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this punctuation sequence is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with letters, digits, numbers, symbols,
        or non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this punctuation sequence.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this punctuation sequence and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_letter(),
            other.is_digit(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_letters(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_word(),
            other.is_non_whitespace(),
        ]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_words():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedPunctsGroupPattern(TranslatedPattern):
    """
    Specialized translated pattern for groups of punctuation characters.

    This subclass of `TranslatedPattern` defines behavior specific to
    punctuation groups (e.g., sequences or phrases of punctuation marks).
    It provides subset and superset checks against other translated
    patterns and supports recommendation logic for generalization when
    combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a punctuation group.
    *other : tuple, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("puncts_group").
    defined_patterns : list of str
        Regex patterns used to match punctuation groups and phrases.
    ref_names : list of str
        Reference names for the defined patterns.
    singular_name : str
        Singular form of this pattern ("puncts").
    singular_pattern : str
        Regex pattern used to match a single punctuation sequence.
    root_name : str
        Root category name for this pattern ("non_whitespaces_or_group").
    """

    def __init__(self, data: str, *other: object) -> None:
        defined_patterns = [
            PATTERN.PUNCTS_OR_PHRASE,
            PATTERN.PUNCTS_OR_GROUP,
            PATTERN.PUNCTS_PHRASE,
            PATTERN.PUNCTS_GROUP,
        ]
        ref_names = [
            "puncts_or_phrase",
            "puncts_or_group",
            "puncts_phrase",
            "puncts_group",
        ]
        super().__init__(
            data,
            *other,
            name=TEXT.PUNCTS_GROUP,
            defined_patterns=defined_patterns,
            ref_names=ref_names,
            singular_name="puncts",
            singular_pattern=PATTERN.PUNCTS,
            root_name="non_whitespaces_or_group",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this punctuation group is a subset of another translated pattern.

        A punctuation group is considered a subset of broader categories such as
        symbol groups, mixed words, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this punctuation group is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_symbols_group(),
            other.is_mixed_words(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this punctuation group is a superset of another translated pattern.

        A punctuation group is considered a superset when the other pattern
        represents a single symbol or a sequence of symbols.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this punctuation group is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_symbol(),
            other.is_symbols(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this punctuation group is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with letters, digits, numbers, words,
        symbols, or non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this punctuation group.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this punctuation group and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_letter(),
            other.is_digit(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_letters(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
        ]):
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedGraphPattern(TranslatedPattern):
    """
    Specialized translated pattern for graphical characters.

    This subclass of `TranslatedPattern` defines behavior specific to
    graphical symbols (e.g., printable non-alphanumeric characters).
    It provides subset and superset checks against other translated
    patterns and supports recommendation logic for generalization
    when combined with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a graphical character.
    *other : list of other arguments, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("graph").
    defined_pattern : str
        Regex pattern used to match graphical characters.
    root_name : str
        Root category name for this pattern ("non_whitespace").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.GRAPH,
            defined_pattern=PATTERN.GRAPH,
            root_name="non_whitespace",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this graph pattern is a subset of another translated pattern.

        A graphical character is considered a subset of broader categories such as
        mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this graph pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_graph(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this graph pattern is a superset of another translated pattern.

        A graphical character is considered a superset when the other pattern
        represents a letter, digit, alphanumeric sequence, or symbol.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this graph pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_digit(),
            other.is_alphabet_numeric(),
            other.is_symbol(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this graph pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with letters, digits, numbers, or words
        produce broader generalized patterns.

        Parameters
        ----------
        other : TranslatedPattern or inherited of TranslatedPattern
            The pattern to combine with this graph pattern.

        Returns
        -------
        TranslatedPattern or inherited of TranslatedPattern
            A generalized translated pattern instance based on the
            relationship between this graph pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letters(), other.is_digits(),
                other.is_number(), other.is_mixed_number(), other.is_word()]):
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_words():
            return TranslatedMixedWordsPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedWordPattern(TranslatedPattern):
    """
    Specialized translated pattern for word inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    words (sequences of letters or alphanumeric tokens). It provides
    subset and superset checks against other translated patterns and
    supports recommendation logic for generalization when combined
    with different pattern types.

    Parameters
    ----------
    data : str
        The input string representing a word.
    *other : list of other data, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("word").
    defined_pattern : str
        Regex pattern used to match words.
    root_name : str
        Root category name for this pattern ("non_whitespaces").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.WORD,
            defined_pattern=PATTERN.WORD,
            root_name="non_whitespaces",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this word pattern is a subset of another translated pattern.

        A word is considered a subset of broader categories such as
        words, mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this word pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this word pattern is a superset of another translated pattern.

        A word is considered a superset when the other pattern
        represents a single letter, multiple letters, digits, or
        an alphanumeric sequence that also qualifies as alphabetic.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this word pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this word pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with numbers, digits, symbols, or
        non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern to combine with this word pattern.

        Returns
        -------
        TranslatedPattern or its subclass
            A generalized translated pattern instance based on the
            relationship between this word pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_graph(),
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_non_whitespace(),
            other.is_symbol(),
            other.is_symbols(),
            other.is_alphabet_numeric()
        ]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedWordsPattern(TranslatedPattern):
    """
    Specialized translated pattern for multiple word inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    sequences of words (phrases or word groups). It provides subset and
    superset checks against other translated patterns and supports
    recommendation logic for generalization when combined with different
    pattern types.

    Parameters
    ----------
    data : str
        The input string representing multiple words.
    *other : tuple, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("words").
    defined_patterns : list of str
        Regex patterns used to match word sequences and groups.
    ref_names : list of str
        Reference names for the defined patterns.
    singular_name : str
        Singular form of this pattern ("word").
    singular_pattern : str
        Regex pattern used to match a single word.
    root_name : str
        Root category name for this pattern ("non_whitespaces_or_group").
    """

    def __init__(self, data: str, *other: object) -> None:
        defined_patterns = [
            PATTERN.WORDS,
            PATTERN.WORD_OR_GROUP,
            PATTERN.PHRASE,
            PATTERN.WORD_GROUP,
        ]
        ref_names = ["words", "word_or_group", "phrase", "word_group"]

        super().__init__(
            data,
            *other,
            name=TEXT.WORDS,
            defined_patterns=defined_patterns,
            ref_names=ref_names,
            singular_name="word",
            singular_pattern=PATTERN.WORD,
            root_name="non_whitespaces_or_group",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this words pattern is a subset of another translated pattern.

        A sequence of words is considered a subset of broader categories such as
        words, mixed words, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this words pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_words(),
            other.is_mixed_words(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this words pattern is a superset of another translated pattern.

        A sequence of words is considered a superset when the other pattern
        represents a single letter, multiple letters, a single word, digits,
        or an alphanumeric sequence.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this words pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters(),
            other.is_word(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this words pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with numbers, digits, symbols, graphs,
        or non-whitespace categories produce broader generalized
        patterns.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern to combine with this words pattern.

        Returns
        -------
        TranslatedPattern or its subclass
            A generalized translated pattern instance based on the
            relationship between this words pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_non_whitespace(),
            other.is_non_whitespaces(),
            other.is_symbol(),
            other.is_symbols(),
            other.is_symbols_group(),
        ]):
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedMixedWordPattern(TranslatedPattern):
    """
    Specialized translated pattern for mixed word inputs.

    This subclass of `TranslatedPattern` defines behavior specific to
    mixed words (sequences containing both letters and digits). It provides
    subset and superset checks against other translated patterns and supports
    recommendation logic for generalization when combined with different
    pattern types.

    Parameters
    ----------
    data : str
        The input string representing a mixed word.
    *other : list of other data, optional
        Additional arguments passed to the base class initializer.

    Attributes
    ----------
    name : str
        Identifier for this pattern type ("mixed_word").
    defined_pattern : str
        Regex pattern used to match mixed words.
    root_name : str
        Root category name for this pattern ("non_whitespaces").
    """

    def __init__(self, data: str, *other: object) -> None:
        super().__init__(
            data,
            *other,
            name=TEXT.MIXED_WORD,
            defined_pattern=PATTERN.MIXED_WORD,
            root_name="non_whitespaces",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this mixed word pattern is a subset of another translated pattern.

        A mixed word is considered a subset of broader categories such as
        mixed words, non-whitespace sequences, and non-whitespace groups.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this mixed word pattern is a subset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_whitespaces(),
            other.is_non_whitespaces_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this mixed word pattern is a superset of another translated pattern.

        A mixed word is considered a superset when the other pattern
        represents letters, digits, alphanumeric sequences, or words.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern instance to compare against.

        Returns
        -------
        bool
            True if this mixed word pattern is a superset of `other`,
            otherwise False.

        Raises
        ------
        RuntimeError
            If `other` is not an instance of `TranslatedPattern`.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters(),
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_alphabet_numeric(),
            other.is_word(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.

        If this mixed word pattern is a subset or superset of `other`,
        a new subset or superset pattern is returned. Otherwise,
        specific combinations with words, symbols, or non-whitespace
        categories produce broader generalized patterns.

        Parameters
        ----------
        other : TranslatedPattern or its subclass
            The pattern to combine with this mixed word pattern.

        Returns
        -------
        TranslatedPattern or its subclass
            A generalized translated pattern instance based on the
            relationship between this mixed word pattern and `other`.

        Raises
        ------
        RuntimeError
            If no recommendation logic is implemented for the given case.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_words():
            return TranslatedMixedWordsPattern(self.data, other.data)

        if any([
            other.is_graph(),
            other.is_non_whitespace(),
            other.is_symbol(),
            other.is_symbols()
        ]):
            return TranslatedNonWhitespacesPattern(self.data, other.data)

        if other.is_symbols_group():
            return TranslatedNonWhitespacesGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedMixedWordsPattern(TranslatedPattern):
    def __init__(self, data, *other):
        defined_patterns = [
            PATTERN.MIXED_WORDS,
            PATTERN.MIXED_WORD_OR_GROUP,
            PATTERN.MIXED_PHRASE,
            PATTERN.MIXED_WORD_GROUP
        ]
        ref_names = ['mixed_words', 'mixed_word_or_group',
                     'mixed_phrase', 'mixed_word_group']
        super().__init__(data, *other, name=TEXT.MIXED_WORDS,
                         defined_patterns=defined_patterns,
                         ref_names=ref_names,
                         singular_name='mixed_word',
                         singular_pattern=PATTERN.MIXED_WORD,
                         root_name='non_whitespaces_or_group')

    def is_subset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_mixed_words() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_letter() or other.is_letters()
        chk |= other.is_digit() or other.is_digits()
        chk |= other.is_alphabet_numeric()
        chk |= other.is_word() or other.is_words() or other.is_mixed_word()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_non_whitespace() or other.is_non_whitespaces()
            case1 |= other.is_symbol() or other.is_symbols() or other.is_symbols_group()

            if case1:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                return self.raise_recommend_exception(other)


class TranslatedNonWhitespacePattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.NON_WHITESPACE,
                         defined_pattern=PATTERN.NON_WHITESPACE,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_letter() or other.is_digit()
        chk |= other.is_alphabet_numeric()
        chk |= other.is_symbol() or other.is_graph()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letters() or other.is_digits() or other.is_symbols()
            case1 |= other.is_number() or other.is_mixed_number()
            case1 |= other.is_word() or other.is_mixed_word()

            case2 = other.is_words() or other.is_mixed_words() or other.is_symbols_group()

            if case1:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case2:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                return self.raise_recommend_exception(other)


class TranslatedNonWhitespacesPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.NON_WHITESPACES,
                         defined_pattern=PATTERN.NON_WHITESPACES,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_digit() or other.is_digits()
        chk |= other.is_number() or other.is_mixed_number()
        chk |= other.is_letter() or other.is_letters()
        chk |= other.is_alphabet_numeric() or other.is_graph()
        chk |= other.is_symbol() or other.is_symbols()
        chk |= other.is_word() or other.is_mixed_word()
        chk |= other.is_non_whitespace()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_symbols_group() or other.is_words() or other.is_mixed_words()

            if case1:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                return self.raise_recommend_exception(other)


class TranslatedNonWhitespacesGroupPattern(TranslatedPattern):
    def __init__(self, data, *other):
        defined_patterns = [
            PATTERN.NON_WHITESPACES_OR_PHRASE,
            PATTERN.NON_WHITESPACES_OR_GROUP,
            PATTERN.NON_WHITESPACES_PHRASE,
            PATTERN.NON_WHITESPACES_GROUP
        ]
        ref_names = ['non_whitespaces_or_phrase', 'non_whitespaces_or_group',
                     'non_whitespaces_phrase', 'non_whitespaces_group']
        super().__init__(data, *other, name=TEXT.NON_WHITESPACES_GROUP,
                         defined_patterns=defined_patterns,
                         ref_names=ref_names,
                         singular_name='non_whitespaces',
                         singular_pattern=PATTERN.NON_WHITESPACES,
                         root_name='non_whitespaces_or_group')

    def is_subset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        chk = other.is_digit() or other.is_digits()
        chk |= other.is_number() or other.is_mixed_number()
        chk |= other.is_letter() or other.is_letters()
        chk |= other.is_alphabet_numeric() or other.is_graph()
        chk |= other.is_symbol() or other.is_symbols() or other.is_symbols_group()
        chk |= other.is_word() or other.is_mixed_word()
        chk |= other.is_words() or other.is_mixed_words()
        chk |= other.is_non_whitespace() or other.is_non_whitespaces()

        return chk

    def recommend(self, other):
        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            return self.raise_recommend_exception(other)
