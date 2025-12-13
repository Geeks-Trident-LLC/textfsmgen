import re

from genericlib import NUMBER
from genericlib import STRING
from genericlib import PATTERN
from genericlib import TEXT
from genericlib import SYMBOL

from genericlib import Misc
from genericlib import MiscFunction


class RuntimeException:
    def raise_runtime_error(self, name='', msg=''):
        name = name.strip()
        obj = name or self
        MiscFunction.raise_runtime_error(obj=obj, msg=msg)

    @classmethod
    def do_raise_runtime_error(cls, obj=None, msg=''):
        MiscFunction.raise_runtime_error(obj=obj, msg=msg)


class LData(RuntimeException):
    def __init__(self, data):
        self.raw_data = str(data)
        self.data = self.raw_data.strip()

    def __call__(self, *args, **kwargs):
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def leading(self):
        leading_spaces = Misc.get_leading_line(self.raw_data)
        return leading_spaces

    @property
    def trailing(self):
        trailing_spaces = Misc.get_trailing_line(self.raw_data)
        return trailing_spaces

    @property
    def is_leading(self):
        chk = self.leading != STRING.EMPTY
        return chk

    @property
    def is_trailing(self):
        chk = self.trailing != STRING.EMPTY
        return chk


class TranslatedPattern(RuntimeException):

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
        chk = self._pattern != STRING.EMPTY
        return chk

    def __call__(self, *args, **kwargs):
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def translated(self):
        chk = self._pattern != STRING.EMPTY
        return chk

    @property
    def actual_name(self):
        if self.defined_patterns and self.ref_names:
            return self.ref_names[self.defined_patterns.index(self._pattern)]
        else:
            return self.name

    @property
    def lessen_name(self):
        if self.defined_patterns and self.ref_names:
            name = self.ref_names[self.defined_patterns.index(self._pattern)]

            tbl = dict(
                puncts_or_group="puncts_or_group",
                puncts_group="puncts_or_group",
                puncts_phrase="puncts_or_group",
                puncts_or_phrase="puncts_or_group",

                word_or_group="word_or_group",
                word_group="word_or_group",
                phrase="word_or_group",
                words="word_or_group",

                mixed_word_or_group="mixed_word_or_group",
                mixed_words="mixed_word_or_group",
                mixed_phrase="mixed_word_or_group",
                mixed_word_group="mixed_word_or_group",

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
        return self._pattern

    @property
    def lessen_pattern(self):
        if self.defined_patterns and self.ref_names:
            lessen_name = self.lessen_name
            lessen_pat = self.defined_patterns[self.ref_names.index(lessen_name)]
            return lessen_pat
        else:
            return self.pattern

    @property
    def root_pattern(self):
        tbl = dict(non_whitespace=PATTERN.NON_WHITESPACE,
                   non_whitespaces=PATTERN.NON_WHITESPACES,
                   non_whitespaces_or_group=PATTERN.NON_WHITESPACES_OR_GROUP)
        root_pattern = tbl.get(self.root_name, PATTERN.NON_WHITESPACES_OR_GROUP)
        return root_pattern

    def process(self):
        if self.defined_patterns:
            is_matched = False
            if self.is_plural():
                for pat in self.defined_patterns[-2:]:
                    is_matched = self.check_matching(pat)
                    if is_matched:
                        self._pattern = pat
                        break
            else:
                for pat in self.defined_patterns:
                    is_matched = self.check_matching(pat)
                    if is_matched:
                        self._pattern = pat
                        break
            if not is_matched:
                self._pattern = STRING.EMPTY
        else:
            is_matched = self.check_matching(self.defined_pattern)
            self._pattern = self.defined_pattern if is_matched else STRING.EMPTY

    def check_matching(self, pattern):
        pat = '%s$' % pattern

        chk = True
        for data in self.lst_of_all_data:
            match = re.match(pat, data)
            chk = chk and bool(match)

        return chk

    def is_digit(self):
        return self.name == TEXT.DIGIT

    def is_digits(self):
        return self.name == TEXT.DIGITS

    def is_number(self):
        return self.name == TEXT.NUMBER

    def is_mixed_number(self):
        return self.name == TEXT.MIXED_NUMBER

    def is_letter(self):
        return self.name == TEXT.LETTER

    def is_letters(self):
        return self.name == TEXT.LETTERS

    def is_alphabet_numeric(self):
        return self.name == TEXT.ALPHABET_NUMERIC

    def is_symbol(self):
        return self.name == TEXT.PUNCT

    def is_symbols(self):
        return self.name == TEXT.PUNCTS

    def is_symbols_group(self):
        return self.name == TEXT.PUNCTS_GROUP

    def is_graph(self):
        return self.name == TEXT.GRAPH

    def is_word(self):
        return self.name == TEXT.WORD

    def is_words(self):
        return self.name == TEXT.WORDS

    def is_mixed_word(self):
        return self.name == TEXT.MIXED_WORD

    def is_mixed_words(self):
        return self.name == TEXT.MIXED_WORDS

    def is_non_whitespace(self):
        return self.name == TEXT.NON_WHITESPACE

    def is_non_whitespaces(self):
        return self.name == TEXT.NON_WHITESPACES

    def is_non_whitespaces_group(self):
        return self.name == TEXT.NON_WHITESPACES_GROUP

    def is_group(self):
        chk = self.is_symbols_group()
        chk |= self.is_words()
        chk |= self.is_mixed_words()
        chk |= self.is_non_whitespaces_group()
        return chk

    def is_group_with_multi_spaces(self):
        if not self.is_group():
            return False

        for data in self.lst_of_all_data:
            if STRING.DOUBLE_SPACES in data.strip():
                return True
        return False

    def is_numeric(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= data.isnumeric()
        return chk

    def is_alphabet(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= data.isalpha()
        return chk

    def is_not_alphabet(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= not data.isalpha()
        return chk

    def is_punctuation(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= data.isprintable() and not data.isalnum()
        return chk

    def is_printable(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= data.isprintable()
        return chk

    def is_subset_of(self, other):
        fmt = 'Need to implement subset verification for (%s, %s)'
        cls_name = Misc.get_instance_class_name(self)
        other_cls_name = Misc.get_instance_class_name(other)
        error = fmt % (cls_name, other_cls_name)
        raise NotImplementedError(error)

    def is_superset_of(self, other):
        fmt = 'Need to implement superset verification for (%s, %s)'
        cls_name = Misc.get_instance_class_name(self)
        other_cls_name = Misc.get_instance_class_name(other)
        error = fmt % (cls_name, other_cls_name)
        raise NotImplementedError(error)

    def get_new_subset(self, other):
        new_instance = other(other.data, other.get_reference_data(self))
        return new_instance

    def get_new_superset(self, other):
        new_instance = self(self.data, self.get_reference_data(other))
        return new_instance

    def is_plural(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= len(re.split(PATTERN.WHITESPACES, data.strip())) > NUMBER.ONE
        return chk

    def is_singular(self):
        chk = True
        for data in self.lst_of_all_data:
            chk &= len(re.split(PATTERN.WHITESPACES, data.strip())) <= NUMBER.ONE
        return chk

    def is_mixing_singular_plural(self):
        chk = not self.is_singular() and not self.is_plural()
        return chk

    def get_singular_data(self):
        singular_data = str.split(self.data, STRING.SPACE_CHAR)[NUMBER.ZERO]
        return singular_data

    def get_plural_data(self):
        for data in self.lst_of_all_data:
            if STRING.SPACE_CHAR in data.strip():
                return data
        else:
            plural_data = '%s %s' % (self.data, self.data)
            return plural_data

    def get_reference_data(self, other):
        if isinstance(other, TranslatedPattern):
            if self.is_subset_of(other) or self.is_superset_of(other):
                return other.data
            else:
                if self.is_plural() and other.is_plural():
                    return self.data
                else:
                    result = self.get_singular_data()
                    return result
        else:
            return self.data

    def raise_recommend_exception(self, other):
        cls_name = Misc.get_instance_class_name(self)
        fmt = 'Need to implement this case (%r, %r) for %s'
        self.raise_runtime_error(
            name='NotImplementRecommendedRTPattern',
            msg=fmt % (self.data, other.data, cls_name),
        )

    def get_readable_snippet(self, var=''):
        if not self.name:
            self.raise_runtime_error(
                name='TranslatedPatternSnippetRTError',
                msg='CANT create snippet without name',
            )

        value = self.data
        value = value.replace(SYMBOL.LEFT_PARENTHESIS, '_SYMBOL_LEFT_PARENTHESIS_')
        value = value.replace(SYMBOL.RIGHT_PARENTHESIS, '_SYMBOL_RIGHT_PARENTHESIS_')

        if var:
            snippet = '%s(var=%s, value=%s)' % (self.actual_name, var, value)
        else:
            snippet = '%s(value=%s)' % (self.actual_name, value)
        return snippet

    def get_regex_pattern(self, var='', is_lessen=False, is_root=False):
        if not self.name:
            self.raise_runtime_error(
                name='TranslatedPatternRegexRTError',
                msg='CANT create regex pattern without name'
            )

        fmt = '(?P<%s>%s)'
        pattern = self.lessen_pattern if is_lessen else self.pattern
        pattern = self.root_pattern if is_root else pattern
        pattern = fmt % (var, pattern) if var else pattern
        return pattern

    def get_template_snippet(self, var='', is_lessen=False, is_root=False):
        if not self.name:
            self.raise_runtime_error(
                name='TranslatedPatternTemplateSnippetRTError',
                msg='CANT create snippet without name'
            )

        var_txt = 'var_%s' % var if var else STRING.EMPTY
        name = self.lessen_name if is_lessen else self.actual_name
        name = self.root_name if is_root else name
        tmpl_snippet = '%s(%s)' % (name, var_txt)
        return tmpl_snippet

    @classmethod
    def do_factory_create(cls, data, *other):
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

        RuntimeException.do_raise_runtime_error(
            obj='FactoryTranslatedPatternRTIssue',
            msg='Need to implement this case (%r, %r)' % (data, other)
        )

    @classmethod
    def recommend_pattern(cls, translated_pat_obj1, translated_pat_obj2):
        generalized_pat = translated_pat_obj1.recommend(translated_pat_obj2)
        return generalized_pat

    @classmethod
    def recommend_pattern_using_data(cls, data1, data2):
        translated_pat_obj1 = cls.do_factory_create(data1)
        translated_pat_obj2 = cls.do_factory_create(data2)
        generalized_pat = translated_pat_obj1.recommend(translated_pat_obj2)
        return generalized_pat


class TranslatedDigitPattern(TranslatedPattern):

    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.DIGIT,
                         defined_pattern=PATTERN.DIGIT,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        chk = other.is_digit() or other.is_digits()
        chk |= other.is_number() or other.is_mixed_number()
        chk |= other.is_alphabet_numeric() or other.is_graph()
        chk |= other.is_word() or other.is_mixed_word()
        chk |= other.is_words() or other.is_mixed_words()
        chk |= other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()
        return chk

    def is_superset_of(self, other):
        return False

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter()
            case2 = other.is_letters()
            case3 = other.is_symbol()
            case4 = other.is_symbols()
            case5 = other.is_symbols_group()

            if case1:
                return TranslatedAlphabetNumericPattern(self.data, other.data)
            elif case2:
                return TranslatedWordPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacePattern(self.data, other.data)
            elif case4:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case5:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedDigitsPattern(TranslatedPattern):

    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.DIGITS,
                         defined_pattern=PATTERN.DIGITS,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_digits()
        chk |= other.is_number() or other.is_mixed_number()
        chk |= other.is_word() or other.is_mixed_word()
        chk |= other.is_words() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_digit()
        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter() or other.is_letters() or other.is_alphabet_numeric()
            case2 = other.is_symbol() or other.is_symbols() or other.is_graph()
            case3 = other.is_symbols_group()
            case4 = other.is_non_whitespace()
            if case1:
                return TranslatedWordPattern(self.data, other.data)
            elif case2:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            elif case4:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedNumberPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.NUMBER,
                         defined_pattern=PATTERN.NUMBER,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_number() or other.is_mixed_number()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_digit() or other.is_digits()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter() or other.is_letters()
            case1 |= other.is_alphabet_numeric() or other.is_graph() or other.is_word()

            case2 = other.is_words() or other.is_symbols_group()
            case3 = other.is_symbol() or other.is_symbols() or other.is_non_whitespace()

            if case1:
                return TranslatedMixedWordPattern(self.data, other.data)
            elif case2:
                return TranslatedMixedWordsPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedMixedNumberPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.MIXED_NUMBER,
                         defined_pattern=PATTERN.MIXED_NUMBER,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_mixed_number() or other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_digit() or other.is_digits() or other.is_number()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter() or other.is_letters()
            case1 |= other.is_alphabet_numeric() or other.is_graph()
            case1 |= other.is_word()

            case2 = other.is_words()
            case3 = other.is_symbol() or other.is_symbols() or other.is_non_whitespace()
            case4 = other.is_symbols_group()

            if case1:
                return TranslatedMixedWordPattern(self.data, other.data)
            elif case2:
                return TranslatedMixedWordsPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case4:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedLetterPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.LETTER,
                         defined_pattern=PATTERN.LETTER,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        chk = other.is_letter() or other.is_letters()
        chk |= other.is_alphabet_numeric() or other.is_graph()
        chk |= other.is_word() or other.is_words()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        return False

    def recommend(self, other):
        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_digit()
            case2 = other.is_digits()
            case3 = other.is_number() or other.is_mixed_number()
            case4 = other.is_symbol()
            case5 = other.is_symbols()
            case6 = other.is_symbols_group()

            if case1:
                return TranslatedAlphabetNumericPattern(self.data, other.data)
            elif case2:
                return TranslatedWordPattern(self.data, other.data)
            elif case3:
                return TranslatedMixedWordPattern(self.data, other.data)
            elif case4:
                return TranslatedGraphPattern(self.data, other.data)
            elif case5:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case6:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedLettersPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.LETTERS,
                         defined_pattern=PATTERN.LETTERS,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_letters() or other.is_word() or other.is_words()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_letter()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_digit() or other.is_digits()

            case2 = other.is_number() or other.is_mixed_number() or other.is_alphabet_numeric()

            case3 = other.is_symbols_group()
            case4 = other.is_symbol() or other.is_symbols() or other.is_non_whitespace()

            if case1:
                return TranslatedWordPattern(self.data, other.data)
            elif case2:
                return TranslatedMixedWordPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            elif case4:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedAlphabetNumericPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.ALPHABET_NUMERIC,
                         defined_pattern=PATTERN.ALPHABET_NUMERIC,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        chk = other.is_alphabet_numeric() or other.is_word() or other.is_words()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_letter() or other.is_letters() or other.is_digit()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_digits()
            case2 = other.is_number() or other.is_mixed_number()
            case3 = other.is_symbol()
            case4 = other.is_symbols()
            case5 = other.is_symbols_group()

            if case1:
                return TranslatedWordPattern(self.data, other.data)
            elif case2:
                return TranslatedMixedWordPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacePattern(self.data, other.data)
            elif case4:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case5:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedPunctPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.PUNCT,
                         defined_pattern=PATTERN.PUNCT,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        chk = other.is_symbol() or other.is_graph()
        chk |= other.is_symbols() or other.is_symbols_group()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        return False

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter() or other.is_digit() or other.is_alphabet_numeric()

            case2 = other.is_letters() or other.is_digits()
            case2 |= other.is_number() or other.is_mixed_number() or other.is_word()

            case3 = other.is_words()

            if case1:
                return TranslatedGraphPattern(self.data)
            elif case2:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedPunctsPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.PUNCTS,
                         defined_pattern=PATTERN.PUNCTS,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_symbols() or other.is_symbols_group()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_symbol()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter() or other.is_digit()
            case1 |= other.is_alphabet_numeric() or other.is_graph()
            case1 |= other.is_letters() or other.is_digits()
            case1 |= other.is_number() or other.is_mixed_number()
            case1 |= other.is_word() or other.is_non_whitespace()

            case2 = other.is_words()

            if case1:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case2:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedPunctsGroupPattern(TranslatedPattern):
    def __init__(self, data, *other):
        defined_patterns = [
            PATTERN.PUNCTS_OR_PHRASE,
            PATTERN.PUNCTS_OR_GROUP,
            PATTERN.PUNCTS_PHRASE,
            PATTERN.PUNCTS_GROUP
        ]
        ref_names = ['puncts_or_phrase', 'puncts_or_group',
                     'puncts_phrase', 'puncts_group']
        super().__init__(data, *other, name=TEXT.PUNCTS_GROUP,
                         defined_patterns=defined_patterns,
                         ref_names=ref_names,
                         singular_name='puncts',
                         singular_pattern=PATTERN.PUNCTS,
                         root_name='non_whitespaces_or_group')

    def is_subset_of(self, other):
        chk = other.is_symbols_group() or other.is_mixed_word()
        chk |= other.is_mixed_words() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_symbol() or other.is_symbols()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letter() or other.is_digit()
            case1 |= other.is_alphabet_numeric() or other.is_graph()
            case1 |= other.is_letters() or other.is_digits()
            case1 |= other.is_number() or other.is_mixed_number()
            case1 |= other.is_word() or other.is_words()

            case2 = other.is_non_whitespace() or other.is_non_whitespaces()

            if case1 or case2:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedGraphPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.GRAPH,
                         defined_pattern=PATTERN.GRAPH,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        chk = other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_letter() or other.is_digit()
        chk |= other.is_alphabet_numeric() or other.is_symbol()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_letters() or other.is_digits()
            case1 |= other.is_number() or other.is_mixed_number() or other.is_word()

            case2 = other.is_words()

            if case1:
                return TranslatedMixedWordPattern(self.data, other.data)
            elif case2:
                return TranslatedMixedWordsPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedWordPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.WORD,
                         defined_pattern=PATTERN.WORD,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_word() or other.is_words()
        chk |= other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_letter() or other.is_letters()
        chk |= other.is_alphabet_numeric() and other.is_alphabet()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_number() or other.is_mixed_number()
            case1 |= other.is_digit() or other.is_digits()
            case1 |= other.is_non_whitespace() or other.is_symbol() or other.is_symbols()
            case1 |= other.is_alphabet_numeric() and other.is_numeric()
            case2 = other.is_symbols_group()

            if case1:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case2:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedWordsPattern(TranslatedPattern):
    def __init__(self, data, *other):
        defined_patterns = [
            PATTERN.WORDS,
            PATTERN.WORD_OR_GROUP,
            PATTERN.PHRASE,
            PATTERN.WORD_GROUP
        ]
        ref_names = ['words', 'word_or_group', 'phrase', 'word_group']
        super().__init__(data, *other, name=TEXT.WORDS,
                         defined_patterns=defined_patterns,
                         ref_names=ref_names,
                         singular_name='word',
                         singular_pattern=PATTERN.WORD,
                         root_name='non_whitespaces_or_group')

    def is_subset_of(self, other):
        chk = other.is_words() or other.is_mixed_words() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_letter() or other.is_letters() or other.is_word()
        chk |= other.is_alphabet_numeric() and other.is_alphabet()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_digit() or other.is_digits()
            case1 |= other.is_number() or other.is_mixed_number()
            case1 |= other.is_non_whitespace() or other.is_non_whitespaces()
            case1 |= other.is_symbol() or other.is_symbols() or other.is_symbols_group()
            case1 |= other.is_alphabet_numeric() and other.is_numeric()

            if case1:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


class TranslatedMixedWordPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.MIXED_WORD,
                         defined_pattern=PATTERN.MIXED_WORD,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_mixed_word() or other.is_mixed_words()
        chk |= other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
        chk = other.is_letter() or other.is_letters()
        chk |= other.is_digit() or other.is_digits()
        chk |= other.is_alphabet_numeric() or other.is_word()

        return chk

    def recommend(self, other):

        if self.is_subset_of(other) or self.is_superset_of(other):
            if self.is_subset_of(other):
                return self.get_new_subset(other)
            else:
                return self.get_new_superset(other)
        else:
            case1 = other.is_words()
            case2 = other.is_non_whitespace() or other.is_symbol() or other.is_symbols()
            case3 = other.is_symbols_group()

            if case1:
                return TranslatedMixedWordsPattern(self.data, other.data)
            elif case2:
                return TranslatedNonWhitespacesPattern(self.data, other.data)
            elif case3:
                return TranslatedNonWhitespacesGroupPattern(self.data, other.data)
            else:
                self.raise_recommend_exception(other)


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
        chk = other.is_mixed_words() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
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
                self.raise_recommend_exception(other)


class TranslatedNonWhitespacePattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.NON_WHITESPACE,
                         defined_pattern=PATTERN.NON_WHITESPACE,
                         root_name='non_whitespace')

    def is_subset_of(self, other):
        chk = other.is_non_whitespace() or other.is_non_whitespaces()
        chk |= other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
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
                self.raise_recommend_exception(other)


class TranslatedNonWhitespacesPattern(TranslatedPattern):
    def __init__(self, data, *other):
        super().__init__(data, *other, name=TEXT.NON_WHITESPACES,
                         defined_pattern=PATTERN.NON_WHITESPACES,
                         root_name='non_whitespaces')

    def is_subset_of(self, other):
        chk = other.is_non_whitespaces() or other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
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
                self.raise_recommend_exception(other)


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
        chk = other.is_non_whitespaces_group()

        return chk

    def is_superset_of(self, other):
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
            self.raise_recommend_exception(other)
