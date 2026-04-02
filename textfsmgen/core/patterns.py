"""
textfsmgen.core.patterns
========================

Core regex pattern definitions for the TextFSM generator.
"""


import re
from typing import Optional, Type
from pathlib import Path
from pathlib import PurePath

import yaml
import string
from copy import copy

from textfsmgen.core.registry import PatternRegistry, SymbolCls
from textfsmgen.exceptions import TextPatternError
from textfsmgen.exceptions import ElementPatternError
from textfsmgen.exceptions import LinePatternError
from textfsmgen.exceptions import raise_exception

from textfsmgen.libs.pattern import validate_pattern, soft_escape
from textfsmgen.libs.text import WHITESPACE_CHARS
from textfsmgen.libs.text import Line

pattern_registry = PatternRegistry()

SYMBOL = SymbolCls()


class VarCls:

    def __init__(self, name='', pattern='', option=''):
        self.name = str(name).strip()
        self.pattern = str(pattern)
        self.option = ','.join(re.split(r'\s*_\s*', str(option).title()))
        self.option = self.option.replace(' ', '')

    @property
    def is_empty(self):
        return self.name == ''

    @property
    def value(self):
        if self.option:
            return f"Value {self.option} {self.name} ({self.pattern})"
        else:
            return f"Value {self.name} ({self.pattern})"

    @property
    def var_name(self) -> str:
        return f"${{{self.name}}}"


class TextPattern(str):
    def __new__(cls, text, as_is=False):
        data = str(text)
        if as_is:
            return str.__new__(cls, data)
        text_pattern = cls.get_pattern(data) if data else ''
        return str.__new__(cls, text_pattern)

    def __init__(self, text, as_is=False):
        self.text = text
        self.as_is = as_is

    def __add__(self, other):
        result = super().__add__(other)
        result_pat = TextPattern(result, as_is=True)
        return result_pat

    def __radd__(self, other):
        if isinstance(other, TextPattern):
            return other.__add__(self)
        else:
            other_pat = TextPattern(other, as_is=True)
            return other_pat.__add__(self)

    @property
    def is_empty(self):
        if self == '':
            return True
        else:
            result = re.match(str(self), '')
            return bool(result)

    @property
    def is_space(self):
        is_space = bool(re.match(self, ' '))
        return is_space

    @property
    def is_empty_or_space(self):
        is_empty = self.is_empty
        is_space = self.is_space
        return is_empty or is_space

    @property
    def is_whitespace(self):
        is_ws = all(True for c in WHITESPACE_CHARS if re.match(self, c))
        return is_ws

    @property
    def is_empty_or_whitespace(self):
        is_empty = self.is_empty
        is_ws = self.is_whitespace
        return is_empty or is_ws

    @classmethod
    def get_pattern(cls, text):
        text_pattern = ''
        start = 0
        m = None
        for m in re.finditer(r'[\r\n]+', text):
            pre_match = text[start:m.start()]
            if pre_match:
                text_pattern += Line(pre_match).convert_to_regex_pattern()
            match = m.group()
            multi = '{1,2}' if len(match) == len(set(match)) else '{2,}'
            text_pattern += f'[\\r\\n]{multi}'
        if m:
            post_match = text[m.end():]
            if post_match:
                text_pattern += Line(post_match).convert_to_regex_pattern()
        else:
            text_pattern = Line(text).convert_to_regex_pattern()

        validate_pattern(text_pattern, exception_cls=TextPatternError)
        return text_pattern

    @classmethod
    def get_pattern_bak(cls, text):
        start = 0
        result = []
        for item in re.finditer(r'\s+', text):
            before_matched = text[start: item.start()]
            before_matched and result.append(soft_escape(before_matched))
            matched = item.group()
            total = len(matched)
            lst = list(matched)
            is_space = lst[0] == ' ' and len(set(lst)) == 1
            is_space and result.append(' ' if total == 1 else ' +')
            not is_space and result.append(r'\s' if total == 1 else r'\s+')
            start = item.end()
        else:
            if result:
                after_matched = text[start:]
                after_matched and result.append(soft_escape(after_matched))
            else:
                result.append(soft_escape(text))

        text_pattern = ''.join(result)

        validate_pattern(text_pattern, exception_cls=TextPatternError)
        return text_pattern

    def lstrip(self, chars=None):
        new_text = self.text.lstrip() if chars is None else self.text.lstrip(chars)
        pattern = TextPattern(new_text)
        return pattern

    def rstrip(self, chars=None):
        new_text = self.text.rstrip() if chars is None else self.text.rstrip(chars)
        pattern = TextPattern(new_text)
        return pattern

    def strip(self, chars=None):
        new_text = self.text.strip() if chars is None else self.text.strip(chars)
        pattern = TextPattern(new_text)
        return pattern

    def add(self, other, as_is=True):
        if isinstance(other, TextPattern):
            result = self + other
        else:
            if isinstance(other, (list, tuple)):
                result = self
                for item in other:
                    if isinstance(item, TextPattern):
                        result = result + item
                    else:
                        item_pat = TextPattern(str(item), as_is=as_is)
                        result = result + item_pat
            else:
                other_pat = TextPattern(str(other), as_is=as_is)
                result = self + other_pat

        return result

    def concatenate(self, *other, as_is=True):
        result = self
        for item in other:
            result = result.add(item, as_is=as_is)
        return result


class ElementPattern(str):
    # patterns
    word_bound_pattern = r'word_bound(_left|_right|_raw)?$'
    head_pattern = r'head(_raw|((_just)?_(whitespaces?|ws|spaces?)(_plus)?))?$'
    tail_pattern = r'tail(_raw|((_just)?_(whitespaces?|ws|spaces?)(_plus)?))?$'
    meta_data_pattern = r'^meta_data_\w+'
    _variable = None

    def __new__(cls, text, as_is=False):
        cls._variable = VarCls()
        cls._or_empty = False
        cls._prepended_pattern = ''
        cls._appended_pattern = ''
        data = str(text)

        if as_is:
            return str.__new__(cls, data)

        pattern = cls.get_pattern(data) if data else ''
        return str.__new__(cls, pattern)

    def __init__(self, text, as_is=False):
        self.text = text
        self.as_is = as_is
        self.variable = self._variable
        self.or_empty = self._or_empty
        self.prepended_pattern = self._prepended_pattern
        self.appended_pattern = self._appended_pattern

        # clear class variable after initialization
        self._variable = VarCls()
        self._or_empty = False
        self._prepended_pattern = ''
        self._appended_pattern = ''

    @classmethod
    def get_pattern(cls, text):
        sep_pat = r'(?P<keyword>\w+)[(](?P<params>.*)[)]$'
        match = re.match(sep_pat, text.strip())
        if match:
            keyword = match.group('keyword')
            params = match.group('params').strip()
            pattern = cls.build_pattern(keyword, params)
        else:
            pattern = soft_escape(text)

        validate_pattern(pattern, exception_cls=ElementPatternError)
        return pattern

    @classmethod
    def build_pattern(cls, keyword, params):
        is_built, raw_pattern = cls.build_raw_pattern(keyword, params)
        if is_built:
            return raw_pattern

        is_built, start_pattern = cls.build_start_pattern(keyword, params)
        if is_built:
            return start_pattern

        is_built, end_pattern = cls.build_end_pattern(keyword, params)
        if is_built:
            return end_pattern

        is_built, symbol_pattern = cls.build_symbol_pattern(keyword, params)
        if is_built:
            return symbol_pattern

        is_built, choice_pattern = cls.build_choice_pattern(keyword, params)
        if is_built:
            return choice_pattern

        is_built, data_pattern = cls.build_data_pattern(keyword, params)
        if is_built:
            return data_pattern

        is_built, custom_pattern = cls.build_custom_pattern(keyword, params)
        if is_built:
            return custom_pattern

        _, default_pattern = cls.build_default_pattern(keyword, params)
        return default_pattern

    @classmethod
    def build_custom_pattern(cls, keyword, params):
        if not pattern_registry.has_keyword(keyword):
            return False, ''

        arguments = re.split(r' *, *', params) if params else []

        lst = [pattern_registry.resolve_pattern(keyword)]

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''
        is_or_either = False
        spaces_occurrence_pat = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        pat = pattern_registry.resolve_pattern(case, default=case)
                        pat not in lst and lst.append(pat)
                else:
                    pat = soft_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        is_multiple = len(lst) > 1
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(
            pattern, word_bound=word_bound, added_parentheses=is_multiple
        )
        if spaces_occurrence_pat:
            fmt = '(%s)|( *%s *)' if is_or_either else '(%s)|(%s)'
            pattern = fmt % (spaces_occurrence_pat, pattern)

        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_symbol_pattern(cls, keyword, params):
        if keyword != 'symbol' or not params.strip():
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        symbol_name, removed_items = '', []
        for arg in arguments:
            if arg.startswith('name='):
                symbol_name = arg[5:]
                removed_items.append(arg)

        if not removed_items:
            return False, ''
        else:
            for item in removed_items:
                item in arguments and arguments.remove(item)

        val = SYMBOL.get(symbol_name, soft_escape(symbol_name))
        lst = [val]

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        pat = pattern_registry.resolve_pattern(case, default=case)
                        pat not in lst and lst.append(pat)
                else:
                    pat = soft_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        is_multiple = len(lst) > 1
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(
            pattern, word_bound=word_bound, added_parentheses=is_multiple
        )
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_choice_pattern(cls, keyword, params):
        if keyword != 'choice':
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        lst = []

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        pat = pattern_registry.resolve_pattern(case, default=case)
                        pat not in lst and lst.append(pat)
                else:
                    pat = soft_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(pattern, word_bound=word_bound)
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_data_pattern(cls, keyword, params):
        if keyword != 'data':
            return False, ''

        arguments = re.split(r' *, *', params) if params else []
        lst = []

        name, vpat = '', r'var_(?P<name>\w+)$'
        or_pat = r'or_(?P<case>[^,]+)'
        is_empty = False
        word_bound = ''
        head = ''
        tail = ''

        for arg in arguments:
            match = re.match(vpat, arg, flags=re.I)
            if match:
                name = match.group('name') if not name else name
            elif re.match(cls.word_bound_pattern, arg):
                if arg == 'word_bound_raw':
                    'word_bound' not in lst and lst.append('word_bound')
                else:
                    word_bound = arg
            elif re.match(cls.head_pattern, arg):
                if arg == 'head_raw':
                    'head' not in lst and lst.append('head')
                else:
                    head = arg
            elif re.match(cls.tail_pattern, arg):
                if arg == 'tail_raw':
                    'tail' not in lst and lst.append('tail')
                else:
                    tail = arg
            elif re.match(cls.meta_data_pattern, arg):
                if arg == 'meta_data_raw':
                    'meta_data' not in lst and lst.append('meta_data')
                else:
                    cls._variable.option = arg.lstrip('meta_data_')
            else:
                match = re.match(or_pat, arg, flags=re.I)
                if match:
                    case = match.group('case')
                    if case == 'empty':
                        is_empty = True
                        cls._or_empty = is_empty
                    else:
                        pat = pattern_registry.resolve_pattern(case, default=case)
                        pat not in lst and lst.append(pat)
                else:
                    pat = soft_escape(arg)
                    pat not in lst and lst.append(pat)

        is_empty and lst.append('')
        pattern = cls.join_list(lst)
        pattern = cls.add_word_bound(pattern, word_bound=word_bound)
        pattern = cls.add_var_name(pattern, name=name)
        pattern = cls.add_head_of_string(pattern, head=head)
        pattern = cls.add_tail_of_string(pattern, tail=tail)
        pattern = pattern.replace('__comma__', ',')
        return True, pattern

    @classmethod
    def build_start_pattern(cls, keyword, params):
        if keyword != 'start':
            return False, ''

        table = dict(space=r'^ *', spaces=r'^ +', space_plus=r'^ +',
                     ws=r'^\s*', ws_plus=r'^\s+',
                     whitespace=r'^\s*', whitespaces=r'^\s+',
                     whitespace_plus=r'^\s+')
        pat = table.get(params, r'^')
        return True, pat

    @classmethod
    def build_end_pattern(cls, keyword, params):
        if keyword != 'end':
            return False, ''

        table = dict(space=r' *$', spaces=r' +$', space_plus=r' +$',
                     ws=r'\s*$', ws_plus=r'\s+$',
                     whitespace=r'\s*$', whitespaces=r'\s+$',
                     whitespace_plus=r'\s+$')
        pat = table.get(params, r'$')
        return True, pat

    @classmethod
    def build_raw_pattern(cls, keyword, params):
        if not params.startswith('raw>>>'):
            return False, ''
        params = re.sub(r'raw>+', '', params, count=1)
        new_params = soft_escape(params)
        pattern = r'{}\({}\)'.format(keyword, new_params)
        return True, pattern

    @classmethod
    def build_default_pattern(cls, keyword, params):
        pattern = soft_escape('{}({})'.format(keyword, params))
        return True, pattern

    @classmethod
    def join_list(cls, lst):
        new_lst = []
        has_ws = False
        if len(lst) > 1:
            for item in lst:
                if ' ' in item or r'\s' in item:
                    has_ws = True
                    if item.startswith('(') and item.endswith(')'):
                        v = item
                    else:
                        if re.match(r' ([?+*]+|([{][0-9,]+[}]))$', item):
                            v = item
                        else:
                            v = '({})'.format(item)
                else:
                    if item:
                        chk1 = '\\' in item
                        chk2 = '[' in item and ']' in item
                        chk3 = '(' in item and ')' in item
                        chk4 = '{' in item and '}' in item
                        if chk1 or chk2 or chk3 or chk4:
                            v = '({})'.format(item)
                        else:
                            v = item
                    else:
                        v = item
                v not in new_lst and new_lst.append(v)
        else:
            new_lst = lst

        has_empty = bool([True for item in new_lst if item == ''])
        if has_empty:
            other_lst = [item for item in new_lst if item]
            result = '|'.join(other_lst)
            result = f"({result}|)" if len(other_lst) == 1 and not has_ws else f"(({result})|)"
            return result
        else:
            result = '|'.join(new_lst)
            result = f"({result})" if len(new_lst) > 1 and has_ws else result
            return result

        # result = '|'.join(new_lst)
        #
        # has_empty = bool([True for i in new_lst if i == ''])
        # if has_empty or len(new_lst) > 1 and has_ws:
        #     result = '({})'.format(result)
        #
        # return result

    @classmethod
    def add_var_name(cls, pattern, name=''):
        if name:
            cls._variable.name = name
            cls._variable.pattern = pattern
            if pattern.startswith('(') and pattern.endswith(')'):
                sub_pat = pattern[1:-1]
                if pattern.endswith('|)'):
                    new_pattern = '(?P<{}>{})'.format(name, sub_pat)
                else:
                    try:
                        re.compile(sub_pat)
                        cls._variable.pattern = sub_pat
                        new_pattern = '(?P<{}>{})'.format(name, sub_pat)
                    except Exception as ex:
                        new_pattern = '(?P<{}>{})'.format(name, pattern)
                        raise_exception(ex, is_skipped=True)
            else:
                new_pattern = '(?P<{}>{})'.format(name, pattern)
            return new_pattern
        return pattern

    @classmethod
    def add_word_bound(cls, pattern, word_bound='', added_parentheses=True):
        if not word_bound:
            return pattern

        has_ws = ' ' in pattern or r'\s' in pattern
        new_pattern = '({})'.format(pattern) if has_ws else pattern
        if added_parentheses:
            if not new_pattern.startswith('(') or not new_pattern.endswith(')'):
                new_pattern = '({})'.format(new_pattern)

        if word_bound == 'word_bound_left':
            new_pattern = r'\b{}'.format(new_pattern)
        elif word_bound == 'word_bound_right':
            new_pattern = r'{}\b'.format(new_pattern)
        else:
            new_pattern = r'\b{}\b'.format(new_pattern)
        return new_pattern

    @classmethod
    def add_head_of_string(cls, pattern, head=''):
        if head:
            case1, case2 = r'^\s*', r'^\s+'
            case3, case4 = r'^ *', r'^ +'
            case5 = r'^'

            case6, case7 = r'\s*', r'\s+'
            case8, case9 = r' *', r' +'

            case10, case11 = r'^\s*', r'^\s+'
            case12, case13 = r'\s*', r'\s+'

            if head == 'head_ws' and not pattern.startswith(case1):
                new_pattern = '{}{}'.format(case1, pattern)
                cls._prepended_pattern = case1
            elif head == 'head_ws_plus' and not pattern.startswith(case2):
                new_pattern = '{}{}'.format(case2, pattern)
                cls._prepended_pattern = case2
            elif head == 'head_space' and not pattern.startswith(case3):
                new_pattern = '{}{}'.format(case3, pattern)
                cls._prepended_pattern = case3
            elif head == 'head_space_plus' and not pattern.startswith(case4):
                new_pattern = '{}{}'.format(case4, pattern)
                cls._prepended_pattern = case4
            elif head == 'head_spaces' and not pattern.startswith(case4):
                new_pattern = '{}{}'.format(case4, pattern)
                cls._prepended_pattern = case4
            elif head == 'head' and not pattern.startswith(case5):
                new_pattern = '{}{}'.format(case5, pattern)
                cls._prepended_pattern = case5
            elif head == 'head_just_ws' and not pattern.startswith(case6):
                new_pattern = '{}{}'.format(case6, pattern)
                cls._prepended_pattern = case6
            elif head == 'head_just_ws_plus' and not pattern.startswith(case7):
                new_pattern = '{}{}'.format(case7, pattern)
                cls._prepended_pattern = case7
            elif head == 'head_just_space' and not pattern.startswith(case8):
                new_pattern = '{}{}'.format(case8, pattern)
                cls._prepended_pattern = case8
            elif head == 'head_just_space_plus' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(case9, pattern)
                cls._prepended_pattern = case9
            elif head == 'head_just_spaces' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(case9, pattern)
                cls._prepended_pattern = case9
            elif head == 'head_whitespace' and not pattern.startswith(case10):
                new_pattern = '{}{}'.format(case10, pattern)
                cls._prepended_pattern = case10
            elif head == 'head_whitespace_plus' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(case11, pattern)
                cls._prepended_pattern = case11
            elif head == 'head_whitespaces' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(case11, pattern)
                cls._prepended_pattern = case11
            elif head == 'head_just_whitespace' and not pattern.startswith(case12):
                new_pattern = '{}{}'.format(case12, pattern)
                cls._prepended_pattern = case12
            elif head == 'head_just_whitespace_plus' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(case13, pattern)
                cls._prepended_pattern = case13
            elif head == 'head_just_whitespaces' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(case13, pattern)
                cls._prepended_pattern = case13
            else:
                new_pattern = pattern
            return new_pattern
        return pattern

    @classmethod
    def add_tail_of_string(cls, pattern, tail=''):
        if tail:
            case1, case2 = r'\s*$', r'\s+$'
            case3, case4 = r' *$', r' +$'
            case5 = r'$'

            case6, case7 = r'\s*', r'\s+'
            case8, case9 = r' *', r' +'

            case10, case11 = r'\s*$', r'\s+$'
            case12, case13 = r'\s*', r'\s+'

            if tail == 'tail_ws' and not pattern.endswith(case1):
                new_pattern = '{}{}'.format(pattern, case1)
                cls._appended_pattern = case1
            elif tail == 'tail_ws_plus' and not pattern.endswith(case2):
                new_pattern = '{}{}'.format(pattern, case2)
                cls._appended_pattern = case2
            elif tail == 'tail_space' and not pattern.endswith(case3):
                new_pattern = '{}{}'.format(pattern, case3)
                cls._appended_pattern = case3
            elif tail == 'tail_space_plus' and not pattern.endswith(case4):
                new_pattern = '{}{}'.format(pattern, case4)
                cls._appended_pattern = case4
            elif tail == 'tail_spaces' and not pattern.endswith(case4):
                new_pattern = '{}{}'.format(pattern, case4)
                cls._appended_pattern = case4
            elif tail == 'tail' and not pattern.endswith(case5):
                new_pattern = '{}{}'.format(pattern, case5)
                cls._appended_pattern = case5
            elif tail == 'tail_just_ws' and not pattern.startswith(case6):
                new_pattern = '{}{}'.format(pattern, case6)
                cls._appended_pattern = case6
            elif tail == 'tail_just_ws_plus' and not pattern.startswith(case7):
                new_pattern = '{}{}'.format(pattern, case7)
                cls._appended_pattern = case7
            elif tail == 'tail_just_space' and not pattern.startswith(case8):
                new_pattern = '{}{}'.format(pattern, case8)
                cls._appended_pattern = case8
            elif tail == 'tail_just_space_plus' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(pattern, case9)
                cls._appended_pattern = case9
            elif tail == 'tail_just_spaces' and not pattern.startswith(case9):
                new_pattern = '{}{}'.format(pattern, case9)
                cls._appended_pattern = case9
            elif tail == 'tail_whitespace' and not pattern.startswith(case10):
                new_pattern = '{}{}'.format(pattern, case10)
                cls._appended_pattern = case10
            elif tail == 'tail_whitespace_plus' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(pattern, case11)
                cls._appended_pattern = case11
            elif tail == 'tail_whitespaces' and not pattern.startswith(case11):
                new_pattern = '{}{}'.format(pattern, case11)
                cls._appended_pattern = case11
            elif tail == 'tail_just_whitespace' and not pattern.startswith(case12):
                new_pattern = '{}{}'.format(pattern, case12)
                cls._appended_pattern = case12
            elif tail == 'tail_just_whitespace_plus' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(pattern, case13)
                cls._appended_pattern = case13
            elif tail == 'tail_just_whitespaces' and not pattern.startswith(case13):
                new_pattern = '{}{}'.format(pattern, case13)
                cls._appended_pattern = case13
            else:
                new_pattern = pattern
            return new_pattern
        return pattern

    def remove_head_of_string(self):
        if self.prepended_pattern and self.startswith('^'):
            pattern = str(self)[len(self.prepended_pattern):]
            new_instance = ElementPattern(pattern, as_is=True)
            new_instance.as_is = False
            new_instance.variable = copy(self.variable)
            new_instance.or_empty = self.or_empty
            new_instance.prepended_pattern = ''
            new_instance.appended_pattern = self.appended_pattern
        else:
            new_instance = copy(self)

        return new_instance

    def remove_tail_of_string(self):
        if self.appended_pattern and self.endswith('$'):
            pattern = str(self)[:-len(self.appended_pattern)]
            new_instance = ElementPattern(pattern, as_is=True)
            new_instance.as_is = False
            new_instance.variable = copy(self.variable)
            new_instance.or_empty = self.or_empty
            new_instance.prepended_pattern = self.prepended_pattern
            new_instance.appended_pattern = ''
        else:
            new_instance = copy(self)

        return new_instance


class LinePattern(str):
    _variables = None

    def __new__(cls, text, prepended_ws=False, appended_ws=False,
                ignore_case=False):
        cls._variables = list()
        cls._items = list()
        data = str(text)
        if data:
            pattern = cls.get_pattern(
                data, prepended_ws=prepended_ws,
                appended_ws=appended_ws, ignore_case=ignore_case
            )
        else:
            pattern = r'^\s*$'
        return str.__new__(cls, pattern)

    def __init__(self, text,
                 prepended_ws=False, appended_ws=False,
                 ignore_case=False):
        self.text = text
        self.prepended_ws = prepended_ws
        self.appended_ws = appended_ws
        self.ignore_case = ignore_case

        self.variables = self._variables
        self.items = self._items

        # clear class variable after initialization
        self._variables = list()
        self._items = list()

    @property
    def statement(self):
        lst = []
        for item in self.items:
            if isinstance(item, ElementPattern):
                if not item.variable.is_empty:
                    lst.append(item.variable.var_name)
                else:
                    lst.append(item)
            else:
                lst.append(item)
        return ''.join(lst)

    @classmethod
    def get_pattern(cls, text,
                    prepended_ws=False, appended_ws=False,
                    ignore_case=False):
        line = str(text)

        lst = []
        start = 0
        m = None
        for m in re.finditer(r'\w+[(][^)]*[)]', line):
            pre_match = m.string[start:m.start()]
            if pre_match:
                lst.append(TextPattern(pre_match))
            elm_pat = ElementPattern(m.group())
            if not elm_pat.variable.is_empty:
                cls._variables.append(elm_pat.variable)
            lst.append(elm_pat)
            start = m.end()
        else:
            if m and start:
                after_match = m.string[start:]
                if after_match:
                    lst.append(TextPattern(after_match))

        if len(lst) == 1 and lst[0].strip() == '':
            return r'^\s*$'
        elif not lst:
            if line.strip() == '':
                return r'^\s*$'
            lst.append(TextPattern(line))

        cls.readjust_if_or_empty(lst)
        cls.ensure_start_of_line_pattern(lst)
        cls.ensure_end_of_line_pattern(lst)
        prepended_ws and cls.prepend_whitespace(lst)
        ignore_case and cls.prepend_ignorecase_flag(lst)
        appended_ws and cls.append_whitespace(lst)
        cls._items = lst
        pattern = ''.join(lst)
        validate_pattern(pattern, exception_cls=LinePatternError)
        return pattern

    @classmethod
    def readjust_if_or_empty(cls, lst):
        if len(lst) < 2:
            return

        total = len(lst)
        ws_pat = ElementPattern('zero_or_whitespaces()')
        insert_indices = []
        for index, item in enumerate(lst[1:], 1):
            prev_item = lst[index-1]
            is_prev_item_text_pat = isinstance(prev_item, (TextPattern, str))
            is_item_elm_pat = isinstance(item, ElementPattern)
            if is_prev_item_text_pat and is_item_elm_pat:
                if item.or_empty:
                    if prev_item.endswith(' '):
                        lst[index-1] = prev_item.rstrip()
                        insert_indices.insert(0, index)
                    elif prev_item.endswith(r'\s'):
                        lst[index-1] = prev_item[:-2]
                        insert_indices.insert(0, index)
                    elif index == total - 1:
                        if prev_item.endswith(' +'):
                            lst[index-1] = prev_item[:-2]
                            insert_indices.insert(0, index)
                        elif prev_item.endswith(r'\s+'):
                            lst[index-1] = prev_item[:-3]
                            insert_indices.insert(0, index)

        for index in insert_indices:
            lst.insert(index, ws_pat)

        index = len(lst) - 1
        is_stopped = False
        insert_indices = []
        while index > 0 and not is_stopped:
            prev_item, item = lst[index-1], lst[index]
            is_prev_item_text_pat = isinstance(prev_item, (TextPattern, str))
            is_item_elm_pat = isinstance(item, ElementPattern)
            if is_prev_item_text_pat and is_item_elm_pat:
                if item.or_empty:
                    if prev_item.endswith(' '):
                        lst[index - 1] = prev_item.rstrip()
                        insert_indices.insert(0, index)
                    elif prev_item.endswith(r'\s') or prev_item.endswith(' +'):
                        lst[index - 1] = prev_item[:-2]
                        insert_indices.insert(0, index)
                    elif prev_item.endswith(r'\s+'):
                        lst[index - 1] = prev_item[:-3]
                        insert_indices.insert(0, index)
            else:
                is_stopped = True
            index -= 2

        for index in insert_indices:
            lst.insert(index, ws_pat)

        index = len(lst) - 1
        is_stopped = False
        is_prev_containing_empty = False
        while index > 0 and not is_stopped:
            prev_item, item = lst[index-1], lst[index]
            is_prev_item_elm_pat = isinstance(prev_item, ElementPattern)
            is_item_text_pat = isinstance(item, (TextPattern, str))
            if is_prev_item_elm_pat and is_item_text_pat:
                if prev_item.or_empty:
                    if item in [' ', ' +', r'\s', r'\s+']:
                        lst[index] = ws_pat
                    is_prev_containing_empty = True
                else:
                    if item in [' ', ' +', r'\s', r'\s+'] and is_prev_containing_empty:
                        lst[index] = ws_pat
                    is_prev_containing_empty = False
            else:
                is_stopped = True
            index -= 2

    @classmethod
    def ensure_start_of_line_pattern(cls, lst):
        if len(lst) < 2:
            return

        curr, nxt = lst[0], lst[1]

        if curr == '^':
            if isinstance(nxt, TextPattern):
                if nxt == ' ':
                    lst.pop(1)
                    return
                if re.match(' [^+*]', nxt):
                    lst[1] = nxt.lstrip()
                    return

        match = re.match(r'(?P<pre_ws>( |\\s)[*+]*)', nxt)
        if re.match(r'(\^|\\A)( |\\s)[*+]*$', curr):
            if isinstance(nxt, TextPattern) and match:
                index = len(match.group('pre_ws'))
                new_val = nxt[index:]
                if new_val == '':
                    lst.pop(1)
                else:
                    lst[1] = new_val

        # clean up any invalid a start of string pattern
        for index, node in enumerate(lst[1:], 1):
            if isinstance(node, ElementPattern) and node.prepended_pattern:
                lst[index] = node.remove_head_of_string()

    @classmethod
    def ensure_end_of_line_pattern(cls, lst):
        if len(lst) < 2:
            return

        last, prev = lst[-1], lst[-2]

        if last == '$':
            if isinstance(prev, TextPattern):
                if prev == ' ':
                    lst.pop(-2)
                    return
                if not re.search(' [+*]$', prev):
                    lst[-2] = prev.rstrip()
                    return

        match = re.search(r'(?P<post_ws>( |\\s)[*+]*)$', prev)
        if re.match(r'( |\\s)[*+]?(\$|\\Z)$', last):
            if isinstance(prev, TextPattern) and match:
                index = len(match.group('post_ws'))
                new_val = prev[:-index]
                if new_val == '':
                    lst.pop(-2)
                else:
                    lst[-2] = new_val

        # clean up any invalid a start of string pattern
        for index, node in enumerate(lst[:-1]):
            if isinstance(node, ElementPattern) and node.appended_pattern:
                lst[index] = node.remove_tail_of_string()

    @classmethod
    def prepend_whitespace(cls, lst):
        if not lst:
            return

        pat = r'(\^|\\A)( |\\s)[*+]?'
        if not re.match(pat, lst[0]):
            lst.insert(0, r'^\s*')

    @classmethod
    def prepend_ignorecase_flag(cls, lst):
        if not lst:
            return

        pat = r'[(][?]i[)]'
        if not re.match(pat, lst[0]):
            lst.insert(0, '(?i)')

    @classmethod
    def append_whitespace(cls, lst):
        if not lst:
            return
        pat = r'( |\\s)[*+]?(\$|\\Z)$'
        if not re.search(pat, lst[-1]):
            lst.append(r'\s*$')
