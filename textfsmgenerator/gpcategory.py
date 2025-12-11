import re

from regexbuilder import TextPattern

from genericlib import STRING, PATTERN, NUMBER, Misc
from textfsmgenerator.gp import LData, TranslatedPattern, RuntimeException
from textfsmgenerator.gpiteractive import IterativeLinePattern
from textfsmgenerator.gpcommon import GPCommon


class BaseCategoryPattern(LData):
    pass


class CategorySepPattern(BaseCategoryPattern):
    def __init__(self, sep):
        super().__init__(sep)

    def to_regex(self):
        node = IterativeLinePattern(self.raw_data)
        pattern = node.to_regex()
        return pattern

    def to_template_snippet(self):
        tmpl_snippet = '%s%s%s' % (self.leading, TextPattern(self.data), self.trailing)
        return tmpl_snippet


class CategorySpacerPattern(BaseCategoryPattern):
    def __init__(self, is_empty=False):
        super().__init__(STRING.EMPTY)
        self.is_empty = is_empty

    def to_regex(self):
        pattern = PATTERN.ZOSPACES if self.is_empty else PATTERN.SPACES
        return pattern

    def to_template_snippet(self):
        tmpl_snippet = 'zero_or_spaces()' if self.is_empty else STRING.DOUBLE_SPACES
        return tmpl_snippet


class CategoryLeftDataPattern(BaseCategoryPattern):

    def __init__(self, data):
        super().__init__(data)

    def to_regex(self):
        pattern = TextPattern(self.raw_data)
        return pattern

    def to_template_snippet(self):
        return self.raw_data


class CategoryRightDataPattern(BaseCategoryPattern):

    def __init__(self, data, var_txt):
        super().__init__(data)
        symbol_n_space_pat = '[ %s' % PATTERN.PUNCTS[NUMBER.ONE:]
        self.var_name = re.sub(symbol_n_space_pat, '_', var_txt).strip('_')

    @property
    def is_empty(self):
        chk = self.data == STRING.EMPTY
        return chk

    def to_regex(self):
        if self.data:
            pat_obj = TranslatedPattern.do_factory_create(self.data)
            pattern = pat_obj.get_regex_pattern(var=self.var_name)
        else:
            pattern = '(?P<%s>.*|)' % self.var_name

        return pattern

    def to_template_snippet(self):
        if self.data:
            pat_obj = TranslatedPattern.do_factory_create(self.data)
            tmpl_snippet = pat_obj.get_template_snippet(var=self.var_name)
        else:
            tmpl_snippet = 'something(var_%s, or_empty)' % self.var_name

        return tmpl_snippet


class CategoryLinePattern(BaseCategoryPattern):
    def __init__(self, line, count=1, separator=':'):
        super().__init__(line)
        self.count = count
        self.separator = separator
        self.left_data = STRING.EMPTY
        self.right_data = STRING.EMPTY
        self._lst = []
        self.process()

    def __len__(self):
        chk = len(self._lst)
        return chk

    @property
    def parsed(self):
        chk = bool(self)
        return chk

    def to_regex(self):
        result = [PATTERN.ZOSPACES if self.is_leading else STRING.EMPTY]
        prev_item = None
        is_last_item_empty = False
        item = None
        for item in self._lst:
            pat = item.to_regex()
            if isinstance(item, CategoryRightDataPattern):
                if item.is_empty and prev_item and not prev_item.is_trailing:
                    pat = '%s%s' % (PATTERN.ZOSPACES, pat)
            result.append(pat)
            prev_item = item
        else:
            if isinstance(item, CategoryRightDataPattern) and item.is_empty:
                is_last_item_empty = True

        if is_last_item_empty:
            result.append(PATTERN.ZOSPACES if self.is_trailing else STRING.EMPTY)

        pattern = str.join(STRING.EMPTY, result)
        replaced_pat = r'( +)(something[\(]var_\w+, or_empty[\)])'
        pattern = re.sub(replaced_pat, r'zero_or_spaces()\2', pattern)

        return pattern

    def to_template_snippet(self):
        result = [self.leading]
        prev_item = None
        item = None
        is_last_item_empty = False
        for item in self._lst:
            _snippet = item.to_template_snippet()
            if isinstance(item, CategoryRightDataPattern):
                if item.is_empty and prev_item and not prev_item.is_trailing:
                    _snippet = 'zero_or_spaces()%s' % _snippet
            result.append(_snippet)
            prev_item = item
        else:
            if isinstance(item, CategoryRightDataPattern) and item.is_empty:
                is_last_item_empty = True

        is_last_item_empty and result.append(self.trailing)

        tmpl_snippet = str.join(STRING.EMPTY, result)
        replaced_pat = r'( +)(something[\(]var_\w+, or_empty[\)])'
        tmpl_snippet = re.sub(replaced_pat, r'zero_or_spaces()\2', tmpl_snippet)

        return tmpl_snippet

    def get_remaining_chars_by_pos(self, char_pos, direction='right'):

        if self.data[char_pos] == STRING.SPACE_CHAR:
            return char_pos

        total, i, j = len(self.data), char_pos, char_pos
        while NUMBER.ZERO <= i < total:
            if self.data[i] == STRING.SPACE_CHAR:
                return j
            j = i
            i = i + NUMBER.ONE if direction == 'right' else i - NUMBER.ONE

    def get_word_by_pos(self, char_pos):
        most_right_pos = self.get_remaining_chars_by_pos(char_pos, direction='right')
        most_left_pos = self.get_remaining_chars_by_pos(char_pos, direction='left')

        word = self.data[most_left_pos:most_right_pos]
        return word

    def get_triple_by_separator(self):
        v1, v2 = str.split(self.data, self.separator, maxsplit=1)
        node1 = LData(v1)
        node2 = LData(v2)
        left = '%s%s' % (node1.leading, node1.data)
        right = '%s%s' % (node2.data, node2.trailing)
        separator = '%s%s%s' % (node1.trailing, self.separator, node2.leading)
        return left, separator, right

    def raise_exception_if_not_category_pattern(self):
        if self.separator not in self.data:
            self.raise_runtime_error(msg='data DOESNT have separator')

        index = self.data.index(self.separator)
        if index == NUMBER.ZERO:
            self.raise_runtime_error(msg='data DOESNT have var text')

        chk_word = self.get_word_by_pos(index)
        if self.is_time_ipv6_or_mac_addr_format(chk_word):
            self.raise_runtime_error(msg='unsupported var text')

    def is_time_ipv6_or_mac_addr_format(self, data):    # noqa
        mac_pat = r'[a-f\d]{1,2}(:[a-f\d]{1,2}){2,5}'
        ipv6_pat = r'[a-f\d]{1,4}(:([a-f\d]{1,4})?)+:[a-f\d]{1,4}'

        is_time = bool(re.search(r'\d+(:\d+)+', data))
        is_mac_addr = bool(re.match(mac_pat, data, re.I))
        is_ipv6 = data.endswith('::') or data.startswith('::')

        is_ipv6 = is_ipv6 or bool(re.match(ipv6_pat, data, re.I))
        chk = is_time or is_mac_addr or is_ipv6
        return chk

    def try_to_get_value(self):
        next_count = self.count - NUMBER.ONE
        if not next_count or not self.right_data.strip():
            return self.right_data, STRING.EMPTY
        else:
            try:
                node = self(self.right_data, count=next_count, separator=self.separator)
                left_data = node.left_data
                pat = PATTERN.ATLONESPACES if STRING.DOUBLE_SPACES in left_data else PATTERN.SPACES
                if STRING.SPACE_CHAR in left_data:
                    val, remaining = re.split(pat, self.right_data, maxsplit=1)
                    return val, remaining
                else:
                    return STRING.EMPTY, self.right_data
            except Exception as ex: # noqa
                items = re.split(PATTERN.SPACES, self.right_data)
                lst = []
                for item in items:
                    chk1 = item == self.separator
                    chk2 = not self.is_time_ipv6_or_mac_addr_format(item)
                    chk2 = chk2 and item.endswith(self.separator)
                    lst.append(TextPattern(item))
                    if chk1 and chk2:
                        break
                other_pat = str.join(PATTERN.SPACES, lst)
                match = re.search(other_pat, self.right_data)
                other_left = match.group()
                other_remaining = self.right_data[len(other_left):]

                if STRING.DOUBLE_SPACES in other_left:
                    pat = PATTERN.ATLONESPACES
                    other_first, other_last = re.split(pat, other_left, maxsplit=1)
                    return other_first, '%s%s' % (other_last, other_remaining)
                else:
                    lst.clear()
                    for item in items:
                        lst.append(item)
                        if self.is_time_ipv6_or_mac_addr_format(item):
                            break

                    other_pat = str.join(PATTERN.SPACES, lst)
                    match = re.search(other_pat, self.right_data)
                    other_left = match.group()
                    other_remaining = self.right_data[len(other_left):]
                    return other_left, other_remaining

    def process(self):
        if not self.count:
            return

        self.raise_exception_if_not_category_pattern()

        var_txt, whole_sep, remaining = self.get_triple_by_separator()
        self.left_data = var_txt
        self.right_data = remaining

        self._lst.append(CategoryLeftDataPattern(var_txt))
        self._lst.append(CategorySepPattern(whole_sep))

        val, other_remaining = self.try_to_get_value()

        value_node = CategoryRightDataPattern(val, var_txt)
        self._lst.append(value_node)

        if other_remaining:
            try:
                other_node = self(other_remaining, count=self.count-1)
                if other_node.parsed:
                    self._lst.append(CategorySpacerPattern())
                    self._lst.append(other_node)
                else:
                    return
            except Exception as ex: # noqa
                return


class CategoryLinesPattern(RuntimeException):
    def __init__(self, *lines, options=None, count=1, separator=':',
                 starting_from=None, ending_to=None):
        self.lines = Misc.get_list_of_lines(*lines)
        self.options = options or dict()
        self.count = count
        self.separator = separator
        self.kwargs = dict(count=self.count, separator=self.separator)
        self.starting_from = starting_from
        self.ending_to = ending_to
        self.index_a = None
        self.index_b = None
        self._lst = []
        self.process()

    @property
    def is_category_format(self):
        chk = any(isinstance(item, CategoryLinePattern) for item in self._lst)
        return chk

    def __len__(self):
        chk = self.is_category_format
        return chk

    def process(self):
        self.index_a = GPCommon.get_line_position_by(self.lines, self.starting_from)
        self.index_b = GPCommon.get_line_position_by(self.lines, self.ending_to)

        if self.index_a and self.index_b and self.index_a >= self.index_b:
            self.index_b = None

        start_index = self.index_a + 1 if self.index_a is not None else self.index_a
        lines = self.lines[start_index:self.index_b]

        for index, line in enumerate(lines):
            try:
                kwargs = self.options.get(str(index), self.kwargs)
                node = CategoryLinePattern(line, **kwargs)
                if node.parsed:
                    self._lst.append(node)
                else:
                    self._lst.append(line)
            except Exception as ex: # noqa
                self._lst.append(line)

    def raise_exception_if_not_category_format(self):
        if not self.is_category_format:
            self.raise_runtime_error(msg='text is not category format')

    def to_regex(self):
        self.raise_exception_if_not_category_format()

        result = []
        for item in self._lst:
            if isinstance(item, CategoryLinePattern):
                result.append(item.to_regex())
            else:
                result.append(TextPattern(item))
        pattern = str.join('(%s)' % PATTERN.CRNL, result)
        return pattern

    def to_template_snippet(self):
        self.raise_exception_if_not_category_format()
        result = []
        for item in self._lst:
            if isinstance(item, CategoryLinePattern):
                result.append(item.to_template_snippet())
            else:
                result.append(item)

        tmpl_snippet = Misc.join_string(*result, separator=STRING.NEWLINE)

        if self.index_a is not None:
            line_snippet = GPCommon.get_fixed_line_snippet(self.lines, index=self.index_a)
            tmpl_snippet = f'{line_snippet} -> Table\nTable\n{tmpl_snippet}'

        if self.index_b is not None:
            line_snippet = GPCommon.get_fixed_line_snippet(self.lines, index=self.index_b)
            tmpl_snippet = f'{tmpl_snippet}\n{line_snippet} -> EOF'

        return tmpl_snippet
