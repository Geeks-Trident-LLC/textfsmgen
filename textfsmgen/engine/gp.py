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

from textfsmgen.libs import PATTERN
from textfsmgen.libs import datatype
from textfsmgen.libs import text

from textfsmgen.exceptions import RuntimeException


class LData(RuntimeException):
    """
    Line number wrapper for string input with utilities to
    inspect leading and trailing whitespace.
    """
    def __init__(self, data):
        self.raw_data = str(data)
        self.data = self.raw_data.strip()

    def __call__(self, *args, **kwargs):
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def leading(self):
        leading_spaces = text.Line.get_leading(self.raw_data)
        return leading_spaces

    @property
    def trailing(self):
        trailing_spaces = text.Line.get_trailing(self.raw_data)
        return trailing_spaces

    @property
    def is_leading(self):
        chk = self.leading != ""
        return chk

    @property
    def is_trailing(self):
        chk = self.trailing != ""
        return chk


class TranslatedPattern(RuntimeException):
    """
    Represents a translated text pattern used in FSM (Finite State Machine)
    generation, providing utilities to normalize, store, and manipulate
    regex-compatible string patterns.
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
        self._pattern = ""
        self.process()

    def __len__(self):
        """Determine whether the pattern is non-empty."""
        chk = self._pattern != ""
        return chk

    def __call__(self, *args, **kwargs):
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def translated(self):
        chk = self._pattern != ""
        return chk

    @property
    def actual_name(self):
        if self.defined_patterns and self.ref_names:
            idx = self.defined_patterns.index(self._pattern)
            return self.ref_names[idx]
        else:
            return self.name

    @property
    def pattern(self):
        """Access the underlying regex pattern string."""
        return self._pattern

    @property
    def root_pattern(self):
        tbl = dict(
            non_ws=PATTERN.NON_WS,
            non_wss=PATTERN.NON_WSS,
            non_wss_group=PATTERN.NON_WSS_GROUP
        )
        root_pattern = tbl.get(self.root_name, PATTERN.NON_WSS_GROUP)
        return root_pattern

    def process(self):
        """
        Resolve and assign the active regex pattern for the instance.
        """
        if self.defined_patterns:
            indices = slice(None, None, -1) if self.is_plural() else slice(None, None)
            defined_patterns = self.defined_patterns[indices]
            for pat in defined_patterns:
                if self.check_matching(pat):
                    self._pattern = pat
                    break
            else:
                self._pattern = ""
        else:
            is_matched = self.check_matching(self.defined_pattern)
            self._pattern = self.defined_pattern if is_matched else ""

    def check_matching(self, pattern):
        """
        Check whether all number entries match the given regex pattern.
        """
        pat = f"{pattern}$"
        is_matched = all(re.match(pat, data) for data in self.lst_of_all_data)
        return is_matched

    def is_digit(self) -> bool:
        return self.name == "digit"

    def is_digits(self) -> bool:
        return self.name == "digits"

    def is_number(self) -> bool:
        return self.name == "number"

    def is_mixed_number(self) -> bool:
        return self.name == "mixed_number"

    def is_letter(self) -> bool:
        return self.name == "letter"

    def is_letters(self) -> bool:
        return self.name == "letters"

    def is_alphabet_numeric(self) -> bool:
        return self.name == "alphabet_numeric"

    def is_punct(self) -> bool:
        return self.name == "punct"

    def is_puncts(self) -> bool:
        return self.name == "puncts"

    def is_puncts_group(self) -> bool:
        return self.name == "puncts_group"

    def is_graph(self) -> bool:
        return self.name == "graph"

    def is_word(self) -> bool:
        return self.name == "word"

    def is_words(self) -> bool:
        return self.name == "words"

    def is_mixed_word(self) -> bool:
        return self.name == "mixed_word"

    def is_mixed_words(self) -> bool:
        return self.name == "mixed_words"

    def is_non_ws(self) -> bool:
        return self.name == "non_ws"

    def is_non_wss(self) -> bool:
        return self.name == "non_wss"

    def is_non_wss_group(self) -> bool:
        return self.name == "non_wss_group"

    def is_group(self):
        chk = (
                self.is_puncts_group()
                or self.is_words()
                or self.is_mixed_words()
                or self.is_non_wss_group()
        )
        return chk

    def is_group_with_multi_spaces(self) -> bool:
        if not self.is_group():
            return False

        return any("  " in data.strip() for data in
                   self.lst_of_all_data)

    def is_numeric(self) -> bool:
        return all(data.isnumeric() for data in self.lst_of_all_data)

    def is_alphabet(self) -> bool:
        return all(data.isalpha() for data in self.lst_of_all_data)

    def is_not_alphabet(self) -> bool:
        return all(not data.isalpha() for data in self.lst_of_all_data)

    def is_punctuation(self) -> bool:
        return all(data.isprintable() and not data.isalnum() for data in
                   self.lst_of_all_data)

    def is_printable(self) -> bool:
        return all(data.isprintable() for data in self.lst_of_all_data)

    def is_subset_of(self, other) -> bool:
        cls_name = datatype.get_class_name(self)
        other_cls_name = datatype.get_class_name(other)
        error = f"Subset verification not implemented for ({cls_name}, {other_cls_name})"
        raise NotImplementedError(error)

    def is_superset_of(self, other) -> bool:
        cls_name = datatype.get_class_name(self)
        other_cls_name = datatype.get_class_name(other)
        error = f"Superset verification not implemented for ({cls_name}, {other_cls_name})"
        raise NotImplementedError(error)

    def get_new_subset(self, other):
        new_instance = other(other.data, other.get_reference_data(self))
        return new_instance

    def get_new_superset(self, other):
        new_instance = self(self.data, self.get_reference_data(other))
        return new_instance

    def is_plural(self) -> bool:
        return all(
            len(re.split(PATTERN.WSS, data.strip())) > 1
            for data in self.lst_of_all_data
        )

    def is_singular(self) -> bool:
        return all(
            len(re.split(PATTERN.WSS, data.strip())) <= 1
            for data in self.lst_of_all_data
        )

    def is_mixing_singular_plural(self) -> bool:
        return not self.is_singular() and not self.is_plural()

    def get_singular_data(self) -> str:
        """
        Extract the first word from the number string.
        """
        return self.data.split(" ")[0]

    def get_plural_data(self) -> str:
        """
        Retrieve plural number from the list of entries.
        """
        for data in self.lst_of_all_data:
            if " " in data.strip():
                return data
        return f"{self.data} {self.data}"

    def get_reference_data(self, other):
        """
        Retrieve reference number based on the relationship with another object.
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
        """
        cls_name = datatype.get_class_name(self)

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
        """
        if not self.name:
            self.raise_runtime_error(
                name="TranslatedPatternSnippetRTError",
                msg="Cannot create snippet without a defined name",
            )

        value = self.data.replace("(", "_SYMBOL_LEFT_PARENTHESIS_")
        value = value.replace(")", "_SYMBOL_RIGHT_PARENTHESIS_")

        if var:
            return f"{self.actual_name}(var={var}, value={value})"
        return f"{self.actual_name}(value={value})"

    def get_regex_pattern(self, var: str = "", is_root: bool = False) -> str:
        """Generate a regex pattern string for the current instance."""
        if not self.name:
            self.raise_runtime_error(
                name="TranslatedPatternRegexRTError",
                msg="Cannot create regex pattern without a defined name",
            )
        pattern = self.root_pattern if is_root else self.pattern

        if var:
            pattern = f"(?P<{var}>{pattern})"

        return pattern

    def get_template_snippet(self, var: str = "", is_root: bool = False) -> str:
        """Generate a template snippet string for the current pattern."""
        if not self.name:
            self.raise_runtime_error(
                name="TranslatedPatternTemplateSnippetRTError",
                msg="Cannot create template snippet without a defined name",
            )

        var_txt = f"var_{var}" if var else ""
        name = self.root_name if is_root else self.actual_name

        return f"{name}({var_txt})"

    @classmethod
    def do_factory_create(cls, data: str, *other):
        """
        Factory method to create a translated pattern instance.
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

            TranslatedNonWSPattern,
            TranslatedNonWSSPattern,
            TranslatedNonWSSGroupPattern,
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
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name="digit",
            defined_pattern=PATTERN.DIGIT,
            root_name="non_ws",
        )

    def is_subset_of(self, other):
        """
        Check if this digit pattern is a subset of another pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_word(),
            other.is_mixed_word(),
            other.is_words(),
            other.is_mixed_words(),
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group()
        ])

    def is_superset_of(self, other):
        """
        Check if this digit pattern is a superset of another pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_digit()

    def recommend(self, other):
        """
        Recommend a generalized pattern when combined with another pattern.
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
        if other.is_punct():
            return TranslatedNonWSPattern(self.data, other.data)
        if other.is_puncts():
            return TranslatedNonWSSPattern(self.data, other.data)
        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedDigitsPattern(TranslatedPattern):
    """
    A translated pattern class specialized for multiple digit inputs.
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name="digits",
            defined_pattern=PATTERN.DIGITS,
            root_name='non_wss'
        )

    def is_subset_of(self, other):
        """
        Determine whether this digit pattern is a subset of another translated pattern.
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
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other):
        """
        Determine whether this digit pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letter(), other.is_letters(),
                other.is_alphabet_numeric()]):
            return TranslatedWordPattern(self.data, other.data)

        if any([other.is_punct(), other.is_puncts(), other.is_graph()]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        if other.is_non_ws():
            return TranslatedNonWSSPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedNumberPattern(TranslatedPattern):
    """
    Specialized translated pattern for numeric inputs.
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name="number",
            defined_pattern=PATTERN.NUMBER,
            root_name='non_wss'
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this number pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_number(),
            other.is_mixed_number(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this number pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits(),
            other.is_number()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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

        if any([other.is_punct(), other.is_puncts(), other.is_non_ws()]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedMixedNumberPattern(TranslatedPattern):
    """
    Specialized translated pattern for mixed numeric inputs.
    """
    def __init__(self, data, *other):
        super().__init__(
            data,
            *other,
            name="mixed_number",
            defined_pattern=PATTERN.MIXED_NUMBER,
            root_name="non_wss",
        )

    def is_subset_of(self, other):
        """
        Determine whether this mixed number pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_mixed_number(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other):
        """
        Determine whether this mixed number pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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

        if any([other.is_punct(), other.is_puncts(), other.is_non_ws()]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedLetterPattern(TranslatedPattern):
    """
    Specialized translated pattern for single-letter inputs.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="letter",
            defined_pattern=PATTERN.LETTER,
            root_name="non_ws",
        )

    def is_subset_of(self, other):
        """
        Determine whether this letter pattern is a subset of another translated pattern.
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
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other):
        """
        Determine whether this letter pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_letter()

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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
        if other.is_punct():
            return TranslatedGraphPattern(self.data, other.data)
        if other.is_puncts():
            return TranslatedNonWSSPattern(self.data, other.data)
        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedLettersPattern(TranslatedPattern):
    """
    Specialized translated pattern for multi-letter inputs.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="letters",
            defined_pattern=PATTERN.LETTERS,
            root_name="non_wss",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this letters pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letters(),
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this letters pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_digit() or other.is_digits() or other.is_alphabet_numeric():
            return TranslatedWordPattern(self.data, other.data)

        if any([other.is_number(), other.is_mixed_number(), other.is_graph()]):
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        if any([other.is_punct(), other.is_puncts(), other.is_non_ws()]):
            return TranslatedNonWSSPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedAlphabetNumericPattern(TranslatedPattern):
    """
    Specialized translated pattern for alphanumeric inputs.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="alphabet_numeric",
            defined_pattern=PATTERN.ALPHABET_NUMERIC,
            root_name="non_ws",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this alphanumeric pattern is a subset of another translated pattern.
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
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this alphanumeric pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_digit(),
            other.is_alphabet_numeric()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_digits():
            return TranslatedWordPattern(self.data, other.data)

        if other.is_number() or other.is_mixed_number():
            return TranslatedMixedWordPattern(self.data, other.data)

        if other.is_punct():
            return TranslatedNonWSPattern(self.data, other.data)

        if other.is_puncts():
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedPunctPattern(TranslatedPattern):
    """
    Specialized translated pattern for punctuation characters.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="punct",
            defined_pattern=PATTERN.PUNCT,
            root_name="non_ws",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this punctuation pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_punct(),
            other.is_graph(),
            other.is_puncts(),
            other.is_puncts_group(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this punctuation pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)
        return other.is_punct()

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([other.is_letter(), other.is_digit(), other.is_alphabet_numeric()]):
            return TranslatedGraphPattern(self.data)

        if any([other.is_letters(), other.is_digits(),
                other.is_number(), other.is_mixed_number(), other.is_word()]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_words():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedPunctsPattern(TranslatedPattern):
    """
    Specialized translated pattern for multiple punctuation characters.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="puncts",
            defined_pattern=PATTERN.PUNCTS,
            root_name="non_wss",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this punctuation sequence is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_puncts(),
            other.is_puncts_group(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this punctuation sequence is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_punct(),
            other.is_puncts()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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
            other.is_non_ws(),
        ]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_words():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedPunctsGroupPattern(TranslatedPattern):
    """
    Specialized translated pattern for groups of punctuation characters.
    """

    def __init__(self, data: str, *other: object):
        defined_patterns = [
            PATTERN.PUNCTS_GROUP,
            PATTERN.PUNCTS_PHRASE,
        ]
        ref_names = [
            "puncts_group",
            "puncts_phrase",
        ]
        super().__init__(
            data,
            *other,
            name="puncts_group",
            defined_patterns=defined_patterns,
            ref_names=ref_names,
            singular_name="puncts",
            singular_pattern=PATTERN.PUNCTS,
            root_name="non_wss_phrase",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this punctuation group is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_puncts_group(),
            other.is_mixed_words(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this punctuation group is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_punct(),
            other.is_puncts(),
            other.is_puncts_group()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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
            other.is_non_ws(),
            other.is_non_wss(),
        ]):
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedGraphPattern(TranslatedPattern):
    """
    Specialized translated pattern for graphical characters.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="graph",
            defined_pattern=PATTERN.GRAPH,
            root_name="non_ws",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this graph pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_graph(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this graph pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_digit(),
            other.is_alphabet_numeric(),
            other.is_punct(),
            other.is_graph()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="word",
            defined_pattern=PATTERN.WORD,
            root_name="non_wss",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this word pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_word(),
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this word pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters(),
            other.is_word()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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
            other.is_non_ws(),
            other.is_punct(),
            other.is_puncts(),
            other.is_alphabet_numeric()
        ]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedWordsPattern(TranslatedPattern):
    """
    Specialized translated pattern for multiple word inputs.
    """

    def __init__(self, data: str, *other: object):
        defined_patterns = [
            PATTERN.WORDS,
            PATTERN.PHRASE,
        ]
        ref_names = [
            "words",
            "phrase",
        ]

        super().__init__(
            data,
            *other,
            name="words",
            defined_patterns=defined_patterns,
            ref_names=ref_names,
            singular_name="word",
            singular_pattern=PATTERN.WORD,
            root_name="non_wss_phrase",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this words pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_words(),
            other.is_mixed_words(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this words pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_letters(),
            other.is_word(),
            other.is_words()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
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
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_punct(),
            other.is_puncts(),
            other.is_puncts_group(),
        ]):
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedMixedWordPattern(TranslatedPattern):
    """
    Specialized translated pattern for mixed word inputs.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="mixed_word",
            defined_pattern=PATTERN.MIXED_WORD,
            root_name="non_wss",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this mixed word pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_mixed_word(),
            other.is_mixed_words(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this mixed word pattern is a superset of another translated pattern.
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
            other.is_mixed_word()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if other.is_words():
            return TranslatedMixedWordsPattern(self.data, other.data)

        if any([
            other.is_graph(),
            other.is_non_ws(),
            other.is_punct(),
            other.is_puncts()
        ]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if other.is_puncts_group():
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedMixedWordsPattern(TranslatedPattern):
    """
    Specialized translated pattern for multiple mixed word inputs.
    """

    def __init__(self, data: str, *other: object):
        defined_patterns = [
            PATTERN.MIXED_WORDS,
            PATTERN.MIXED_PHRASE,
        ]
        ref_names = [
            "mixed_words",
            "mixed_phrase",
        ]

        super().__init__(
            data,
            *other,
            name="mixed_words",
            defined_patterns=defined_patterns,
            ref_names=ref_names,
            singular_name="mixed_word",
            singular_pattern=PATTERN.MIXED_WORD,
            root_name="non_wss_phrase",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this mixed words pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_mixed_words(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this mixed words pattern is a superset of another translated pattern.
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
            other.is_words(),
            other.is_mixed_word(),
            other.is_mixed_words()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_graph(),
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_punct(),
            other.is_puncts(),
            other.is_puncts_group(),
        ]):
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedNonWSPattern(TranslatedPattern):
    """
    Specialized translated pattern for non-whitespace characters.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="non_ws",
            defined_pattern=PATTERN.NON_WS,
            root_name="non_ws",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this non-whitespace pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this non-whitespace pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_letter(),
            other.is_digit(),
            other.is_alphabet_numeric(),
            other.is_punct(),
            other.is_graph(),
            other.is_non_ws()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_letters(),
            other.is_digits(),
            other.is_puncts(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_word(),
            other.is_mixed_word(),
        ]):
            return TranslatedNonWSSPattern(self.data, other.data)

        if any([
            other.is_words(),
            other.is_mixed_words(),
            other.is_puncts_group(),
        ]):
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedNonWSSPattern(TranslatedPattern):
    """
    Specialized translated pattern for non-whitespace sequences.
    """

    def __init__(self, data: str, *other: object):
        super().__init__(
            data,
            *other,
            name="non_wss",
            defined_pattern=PATTERN.NON_WSS,
            root_name="non_wss",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this non-whitespaces pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this non-whitespaces pattern is a superset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_letter(),
            other.is_letters(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_punct(),
            other.is_puncts(),
            other.is_word(),
            other.is_mixed_word(),
            other.is_non_ws(),
            other.is_non_wss()
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        if any([
            other.is_puncts_group(),
            other.is_words(),
            other.is_mixed_words(),
        ]):
            return TranslatedNonWSSGroupPattern(self.data, other.data)

        return self.raise_recommend_exception(other)


class TranslatedNonWSSGroupPattern(TranslatedPattern):
    """
    Specialized translated pattern for groups of non-whitespace sequences.
    """

    def __init__(self, data: str, *other: object):
        defined_patterns = [
            PATTERN.NON_WSS_GROUP,
            PATTERN.NON_WSS_PHRASE,

        ]
        ref_names = [
            "non_wss_group",
            "non_wss_phrase",
        ]

        super().__init__(
            data,
            *other,
            name="non_wss_group",
            defined_patterns=defined_patterns,
            ref_names=ref_names,
            singular_name="non_wss",
            singular_pattern=PATTERN.NON_WSS,
            root_name="non_wss_phrase",
        )

    def is_subset_of(self, other) -> bool:
        """
        Determine whether this non-whitespaces group pattern is a subset of another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return other.is_non_wss_group()

    def is_superset_of(self, other) -> bool:
        """
        Determine whether this non-whitespaces group pattern is a superset of
        another translated pattern.
        """
        if not isinstance(other, TranslatedPattern):
            self.raise_recommend_exception(other)

        return any([
            other.is_digit(),
            other.is_digits(),
            other.is_number(),
            other.is_mixed_number(),
            other.is_letter(),
            other.is_letters(),
            other.is_alphabet_numeric(),
            other.is_graph(),
            other.is_punct(),
            other.is_puncts(),
            other.is_puncts_group(),
            other.is_word(),
            other.is_mixed_word(),
            other.is_words(),
            other.is_mixed_words(),
            other.is_non_ws(),
            other.is_non_wss(),
            other.is_non_wss_group(),
        ])

    def recommend(self, other):
        """
        Recommend a generalized translated pattern when combined with another pattern.
        """
        if self.is_subset_of(other):
            return self.get_new_subset(other)
        if self.is_superset_of(other):
            return self.get_new_superset(other)

        return self.raise_recommend_exception(other)
