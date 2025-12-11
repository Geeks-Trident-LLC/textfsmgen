import re
from difflib import ndiff
from itertools import combinations

from regexbuilder import TextPattern        # noqa
from regexbuilder import ElementPattern     # noqa
from regexbuilder import LinePattern        # noqa

from genericlib import STRING, PATTERN, Misc, NUMBER, INDEX
from genericlib import Text
from textfsmgenerator.gp import RuntimeException, TranslatedPattern


class NDiffBaseText:
    def __init__(self, txt):
        self._pattern = STRING.EMPTY
        self._snippet = STRING.EMPTY
        self._lst = []
        self._lst_other = []
        self._is_common = False
        self._is_changed = False

        if txt.startswith(STRING.DOUBLE_SPACES):
            self._lst.append(txt.lstrip(STRING.SPACE_CHAR))
            self._is_common = True

        if txt.startswith('- ') or txt.startswith('+ '):
            txt.startswith('- ') and self._lst.append(txt.lstrip('- '))
            txt.startswith('+ ') and self._lst_other.append(txt.lstrip('+ '))
            self._is_changed = True

    def __len__(self):
        chk = bool(len(self._lst) or len(self._lst_other))
        return chk

    @property
    def is_common(self):
        return self._is_common

    @property
    def is_changed(self):
        return self._is_changed

    @property
    def name(self):
        return STRING.EMPTY

    @property
    def lst(self):
        return self._lst

    @property
    def lst_other(self):
        return self._lst_other

    def is_same_type(self, other):
        if self.name:
            chk = self.name == other.name
            return chk
        else:
            return False

    def extend(self, other):
        self._lst.extend(other.lst)
        self._lst_other.extend(other.lst_other)

    def readjust_lst(self, *lst_of_txt):
        if lst_of_txt:
            self._lst.clear()
            self._lst.extend(txt for txt in lst_of_txt if txt)

    def readjust_lst_other(self, *lst_of_other_txt):
        if lst_of_other_txt:
            self._lst_other.clear()
            self._lst_other.extend(txt for txt in lst_of_other_txt if txt)

    @classmethod
    def do_factory_create(cls, txt):
        if txt.startswith(STRING.DOUBLE_SPACES):
            return NDiffCommonText(txt)
        else:
            changed_node = NDiffChangedText(txt)
            node = changed_node if changed_node else None
        return node


class NDiffCommonText(NDiffBaseText):
    @property
    def name(self):
        name_ = 'ndiff_common_text' if self else STRING.EMPTY
        return name_

    def get_pattern(self, whitespace=' '):
        txt = str.join(STRING.DOUBLE_SPACES, self.lst)
        pattern = TextPattern(txt) if txt else STRING.EMPTY
        self._pattern = pattern.replace(STRING.SPACE_CHAR, whitespace)
        return self._pattern

    def get_snippet(self, whitespace=' '):
        is_ws = whitespace == PATTERN.WHITESPACE
        spacer = f'\t ' if is_ws else STRING.DOUBLE_SPACES
        snippet = str.join(spacer, self.lst)
        self._snippet = snippet
        return snippet


class NDiffChangedText(NDiffBaseText):
    @property
    def name(self):
        name_ = 'ndiff_changed_text' if self else STRING.EMPTY
        return name_

    @property
    def is_containing_empty_changed(self):
        if self.lst and self.lst_other:
            return False
        elif self.lst or self.lst_other:
            return True
        else:
            return False

    def get_pattern(self, var='', label=None, is_lessen=False, is_root=False):
        var = var.replace('v', f'v{label}', NUMBER.ONE) if label else var

        txt1 = str.join(STRING.DOUBLE_SPACES, self.lst)
        txt2 = str.join(STRING.DOUBLE_SPACES, self.lst_other)
        if txt1 or txt2:
            args = [txt1, txt2] if txt1 and txt2 else [txt1] if txt1 else [txt2]
            factory = TranslatedPattern.do_factory_create(*args)
            pattern = factory.lessen_pattern if is_lessen else factory.pattern
            pattern = factory.root_pattern if is_root else pattern
        else:
            pattern = STRING.EMPTY

        if var:
            fmt = "(?P<%s>(%s)|)" if self.is_containing_empty_changed else "(?P<%s>%s)"
            pattern = fmt % (var, pattern)
        else:
            if pattern:
                pattern = f"(({pattern})|)" if self.is_containing_empty_changed else pattern
        return pattern

    def get_snippet(self, var='', label=None, is_lessen=False, is_root=False):
        var = var.replace('v', f'v{label}', NUMBER.ONE) if label else var

        txt1 = str.join(STRING.DOUBLE_SPACES, self.lst)
        txt2 = str.join(STRING.DOUBLE_SPACES, self.lst_other)
        if txt1 or txt2:
            args = [txt1, txt2] if txt1 and txt2 else [txt1] if txt1 else [txt2]
            factory = TranslatedPattern.do_factory_create(*args)
            kwargs = dict(var=var, is_lessen=is_lessen, is_root=is_root)
            self._snippet = factory.get_template_snippet(**kwargs)
            if self.is_containing_empty_changed:
                self._snippet = '%s, or_empty)' % self._snippet[:-1]

        return self._snippet


class NDiffLinePattern:
    def __init__(self, line_a, line_b, whitespace=None, label=None,
                 is_lessen=False, is_root=False):
        self.whitespace = whitespace
        if not self.whitespace:
            is_ws = any(Misc.is_whitespace_in_line(line) for line in [line_a, line_b])
            self.whitespace = PATTERN.WHITESPACE if is_ws else PATTERN.SPACE

        self.label = label
        self.is_lessen = is_lessen
        self.is_root = is_root

        self.is_leading = Misc.is_leading_line(line_a)
        self.is_leading |= Misc.is_leading_line(line_b)
        self.are_leading = Misc.is_leading_line(line_a)
        self.are_leading &= Misc.is_leading_line(line_b)

        self.is_trailing = Misc.is_trailing_line(line_a)
        self.is_trailing |= Misc.is_trailing_line(line_b)
        self.are_trailing = Misc.is_trailing_line(line_a)
        self.are_trailing &= Misc.is_trailing_line(line_b)

        multi = '+' if self.are_leading else '*'
        ws = self.whitespace
        self.leading_whitespace = f'{ws}{multi}' if self.is_leading else STRING.EMPTY

        multi = '+' if self.are_trailing else '*'
        self.trailing_whitespace = f'{ws}{multi}' if self.is_trailing else STRING.EMPTY

        self.line_a = line_a
        self.line_b = line_b

        self._line_a = self.line_a.strip()
        self._line_b = self.line_b.strip()

        self._is_diff = False
        self._pattern = STRING.EMPTY
        self._snippet = STRING.EMPTY
        self.process()

    def __len__(self):
        return self._pattern != STRING.EMPTY

    def __call__(self, *args, **kwargs):
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def is_diff(self):
        return self._is_diff

    @property
    def pattern(self):
        leading_ws, trailing_ws = self.leading_whitespace, self.trailing_whitespace
        pattern = f'{leading_ws}{self._pattern}{trailing_ws}'
        return pattern

    @property
    def snippet(self):
        if self.is_diff:
            leading_snippet, trailing_snippet = 'start()', 'end()'
            whitespace = 'whitespace' if self.whitespace == r'\s' else 'space'
            if self.is_leading:
                new_ws = f'{whitespace}s' if self.are_leading else whitespace
                leading_snippet = leading_snippet.replace('()', f'({new_ws})')
            if self.is_trailing:
                new_ws = f'{whitespace}s' if self.are_trailing else whitespace
                trailing_snippet = trailing_snippet.replace('()', f'({new_ws})')
            snippet = f'{leading_snippet} {self._snippet} {trailing_snippet}'
            return snippet
        else:
            return self._snippet

    def analyze_and_parse_empty_case(self):
        is_equal = self._line_a == self._line_b
        is_empty = self._line_a == STRING.EMPTY

        if is_empty and is_equal:
            if self.is_leading or self.is_trailing:
                self._pattern = f'{self.whitespace}+'
            self._snippet = self.line_a
            return True
        return False

    def analyze_and_parse_identical_case(self):
        if self._line_a == self._line_b:
            self._pattern = TextPattern(self._line_a)
            self._snippet = self.line_a
            return True
        else:
            lst_a = re.split(f'{self.whitespace}+', self._line_a)
            lst_b = re.split(f'{self.whitespace}+', self._line_b)
            if lst_a == lst_b:
                new_lst = [TextPattern(item) for item in lst_a]
                self._pattern = str.join(f'{self.whitespace}+', new_lst)
                return True
        return False

    def build_list_of_diff(self):
        lst_a = re.split(PATTERN.WHITESPACES, self._line_a)
        lst_b = re.split(PATTERN.WHITESPACES, self._line_b)
        diff = ndiff(lst_a, lst_b)
        lst = [item for item in diff if not item.startswith('? ')]
        result = []
        for item in lst:
            node = NDiffBaseText.do_factory_create(item)
            if result:
                prev_node = result[-NUMBER.ONE]
                if prev_node.is_same_type(node):
                    prev_node.extend(node)
                else:
                    result.append(node)
            else:
                result.append(node)
        return result

    def build_pattern_from_diff_list(self, lst):    # noqa
        kwargs = dict(label=self.label, is_lessen=self.is_lessen, is_root=self.is_root)

        total = len(lst)
        if total == NUMBER.ONE:
            item = lst[INDEX.ZERO]
            if item.is_changed:
                pattern = item.get_pattern(var='v0', **kwargs)
            else:
                pattern = item.get_pattern(whitespace=self.whitespace)
            return pattern
        else:
            result = []
            count = 0
            spacer = PATTERN.WHITESPACES if self.whitespace == PATTERN.WHITESPACE else PATTERN.SPACES
            for index, item in enumerate(lst):
                if index <= total - NUMBER.TWO:
                    if item.is_changed:
                        pat = item.get_pattern(var='v%s' % count, **kwargs)
                        count += 1
                        if item.is_containing_empty_changed:
                            result.extend([pat, '(%s)?' % spacer])
                        else:
                            result.extend([pat, spacer])
                    else:
                        pat = item.get_pattern(whitespace=self.whitespace)
                        result.extend([pat, spacer])
                else:
                    if item.is_changed:
                        pat = item.get_pattern(var='v%s' % count, **kwargs)
                        if item.is_containing_empty_changed:
                            result.pop()
                            result.extend(['(%s)?' % spacer, pat])
                        else:
                            result.append(pat)
                    else:
                        pat = item.get_pattern(whitespace=self.whitespace)
                        result.append(pat)
            pattern = str.join(STRING.EMPTY, result)
            return pattern

    def build_snippet_from_diff_list(self, lst):    # noqa
        result = []
        count = NUMBER.ZERO
        for index, item in enumerate(lst):
            count += NUMBER.ONE if item.is_changed else NUMBER.ZERO
            if item.is_changed:
                kwargs = dict(var=f'v{count}', label=self.label,
                              is_lessen=self.is_lessen, is_root=self.is_root)
                snippet_ = item.get_snippet(**kwargs)
            else:
                snippet_ = item.get_snippet(whitespace=self.whitespace)
            result.append(snippet_)
        snippet = str.join(STRING.DOUBLE_SPACES, result)
        return snippet

    def analyze_and_parse_diff_case(self):

        if self.analyze_and_parse_empty_case():
            return False
        elif self.analyze_and_parse_identical_case():
            return False
        else:
            self._is_diff = True
            lst = self.build_list_of_diff()
            self._pattern = self.build_pattern_from_diff_list(lst)
            self._snippet = self.build_snippet_from_diff_list(lst)
            return True

    def process(self):
        is_empty = self.analyze_and_parse_empty_case()
        is_similar = not is_empty and self.analyze_and_parse_identical_case()
        not is_similar and self.analyze_and_parse_diff_case()


class DiffLinePattern(RuntimeException):
    def __init__(self, line1, line2, *other_lines, label=None):
        self.label = label
        self.raw_lines = []
        self.lines = []
        self._is_diff = False
        self._pattern = STRING.EMPTY
        self._snippet = STRING.EMPTY
        self.prepare(line1, line2, *other_lines)
        self.process()

    def __len__(self):
        chk = bool(len(self._pattern))
        return int(chk)

    @property
    def is_diff(self):
        return self._is_diff

    @property
    def pattern(self):
        pattern = f'{self.leading_whitespace}{self._pattern}{self.trailing_whitespace}'
        return pattern

    @property
    def snippet(self):
        if self.is_diff:
            leading_snippet, trailing_snippet = 'start()', 'end()'
            whitespace = 'whitespace' if self.whitespace == r'\s' else 'space'
            if self.is_leading:
                new_ws = f'{whitespace}s' if self.are_leading else whitespace
                leading_snippet = leading_snippet.replace('()', f'({new_ws})')
            if self.is_trailing:
                new_ws = f'{whitespace}s' if self.are_trailing else whitespace
                trailing_snippet = trailing_snippet.replace('()', f'({new_ws})')

            pat = r'^(start[(]\w*[)]) (?P<snippet>.+) (end[(]\w*[)])$'
            match = re.match(pat, self._snippet)
            if match:
                snippet_ = match.group('snippet')
                snippet = f'{leading_snippet} {snippet_} {trailing_snippet}'
            else:
                snippet = f'{leading_snippet} {self._snippet} {trailing_snippet}'
            return snippet
        else:
            return self._snippet

    @property
    def are_leading(self):
        chk = all(Misc.is_leading_line(line) for line in self.raw_lines)
        return chk

    @property
    def are_trailing(self):
        chk = all(Misc.is_trailing_line(line) for line in self.raw_lines)
        return chk

    @property
    def is_leading(self):
        chk = any(Misc.is_leading_line(line) for line in self.raw_lines)
        return chk

    @property
    def is_trailing(self):
        chk = any(Misc.is_trailing_line(line) for line in self.raw_lines)
        return chk

    @property
    def is_whitespace_in_line(self):
        chk = any(Misc.is_whitespace_in_line(line) for line in self.raw_lines)
        return chk

    @property
    def whitespace(self):
        return PATTERN.WHITESPACE if self.is_whitespace_in_line else PATTERN.SPACE

    @property
    def leading_whitespace(self):
        multi = '+' if self.are_leading else '*'
        pattern = f'{self.whitespace}{multi}' if self.is_leading else STRING.EMPTY
        return pattern

    @property
    def trailing_whitespace(self):
        multi = '+' if self.are_trailing else '*'
        pattern = f'{self.whitespace}{multi}' if self.is_trailing else STRING.EMPTY
        return pattern

    def reset(self):
        self.lines.clear()
        self._pattern = STRING.EMPTY

    def prepare(self, line1, line2, *other_lines):

        lst = [line1, line2] + list(other_lines)

        raw_lines = []
        lines = []

        for line in lst:
            trim_line = line.strip()
            if trim_line:
                line not in raw_lines and raw_lines.append(line)
                trim_line not in lines and lines.append(trim_line)

        if len(lines) < NUMBER.TWO:
            fmt = ('CANT form pattern because provided '
                   'lines are less than two\n%s')
            lst = ['Line 1: %r' % line1, 'Line 2: %r' % line2]
            if other_lines:
                lst.append('Other Lines: %r' % other_lines)

            self.raise_runtime_error(msg=fmt % str.join(STRING.NEWLINE, lst))
        else:
            self.reset()
            self.lines.extend(lines)
            self.raw_lines.extend(raw_lines)

    def get_pattern_btw_two_lines(self, line_a, line_b, is_lessen=False, is_root=False):
        diff_line_obj = NDiffLinePattern(
            line_a, line_b, label=self.label, whitespace=f'{self.whitespace}',
            is_lessen=is_lessen, is_root=is_root
        )
        pattern = diff_line_obj.pattern
        self._is_diff = diff_line_obj.is_diff
        return pattern

    def get_snippet_btw_two_lines(self, line_a, line_b, is_lessen=False, is_root=False):    # noqa
        diff_line_obj = NDiffLinePattern(
            line_a, line_b, label=self.label, whitespace=f'{self.whitespace}',
            is_lessen=is_lessen, is_root=False
        )
        snippet = diff_line_obj.snippet
        return snippet

    def is_matched_all(self, pattern):
        for line in self.lines:
            match = re.match(pattern, line)
            if not match:
                return False
            else:
                if match.group() != line:
                    return False
        return True

    def reconstruct_pattern_and_snippet(self):
        lst = []
        for line in self.lines:
            match = re.match(self._pattern, line)
            other_lst = ['(?P<c0>.*)']
            key = ''
            for key, val in match.groupdict().items():
                val = re.escape(val)
                other_lst.append(f'(?P<{key}>{val})')
                other_lst.append(f'(?P<c{key}>.+)')
            else:
                other_lst.pop()
                other_lst.append(f'(?P<c{key}>.*)')

            generic_pattern = Misc.join_string(*other_lst)
            match = re.match(generic_pattern, line)

            if lst:
                for index, pair in enumerate(match.groupdict().items()):
                    key, val = pair
                    lst[index].add(val)
            else:
                for key, val in match.groupdict().items():
                    if key.startswith('c'):
                        lst.append(DText(val))
                    else:
                        lst.append(DChange(val, var=key))

        snippet = str.join('', [item.get_snippet() for item in lst])
        self._snippet = f'start() {snippet} end()'
        self._pattern = LinePattern(snippet)

    def process(self):
        lines_count = len(self.lines)

        pairs = list(combinations(range(lines_count), NUMBER.TWO))

        lst = []

        # first pass
        for i, j in pairs:
            line_a = self.lines[i]
            line_b = self.lines[j]
            pattern = self.get_pattern_btw_two_lines(line_a, line_b)
            snippet = self.get_snippet_btw_two_lines(line_a, line_b)
            lst.append(pattern)
            if self.is_matched_all(pattern):
                self._pattern = pattern
                self._snippet = snippet
                self.reconstruct_pattern_and_snippet()
                return

        # if first pass failed, run second pass with is_lessen is True
        for i, j in pairs:
            line_a = self.lines[i]
            line_b = self.lines[j]
            pattern = self.get_pattern_btw_two_lines(line_a, line_b, is_lessen=True)
            snippet = self.get_snippet_btw_two_lines(line_a, line_b, is_lessen=True)
            lst.append(pattern)
            if self.is_matched_all(pattern):
                self._pattern = pattern
                self._snippet = snippet
                self.reconstruct_pattern_and_snippet()
                return

        # if second pass failed, run third pass with is_root is True
        for i, j in pairs:
            line_a = self.lines[i]
            line_b = self.lines[j]
            pattern = self.get_pattern_btw_two_lines(line_a, line_b, is_root=True)
            snippet = self.get_snippet_btw_two_lines(line_a, line_b, is_root=True)
            lst.append(pattern)
            if self.is_matched_all(pattern):
                self._pattern = pattern
                self._snippet = snippet
                self.reconstruct_pattern_and_snippet()
                return

        fmt = 'built pattern(s) did not match text\n  %s'
        self.raise_runtime_error(msg=fmt % str.join('\n  ', [repr(item) for item in lst]))


class CommonDiffLinePattern(RuntimeException):
    def __init__(self, *lines, label=None):
        self.raw_lines = lines
        self.lines = [line.strip() for line in lines if line.strip()]
        self.label = label
        self._is_diff = False
        self._pattern = ''
        self._snippet = ''
        self.process()

    @property
    def are_leading(self):
        chk = all(Misc.is_leading_line(line) for line in self.raw_lines)
        return chk

    @property
    def are_trailing(self):
        chk = all(Misc.is_trailing_line(line) for line in self.raw_lines)
        return chk

    @property
    def is_leading(self):
        chk = any(Misc.is_leading_line(line) for line in self.raw_lines)
        return chk

    @property
    def is_trailing(self):
        chk = any(Misc.is_trailing_line(line) for line in self.raw_lines)
        return chk

    @property
    def is_whitespace_in_line(self):
        chk = any(Misc.is_whitespace_in_line(line) for line in self.raw_lines)
        return chk

    @property
    def whitespace(self):
        return PATTERN.WHITESPACE if self.is_whitespace_in_line else PATTERN.SPACE

    @property
    def leading_whitespace(self):
        multi = '+' if self.are_leading else '*'
        pattern = f'{self.whitespace}{multi}' if self.is_leading else STRING.EMPTY
        return pattern

    @property
    def trailing_whitespace(self):
        multi = '+' if self.are_trailing else '*'
        pattern = f'{self.whitespace}{multi}' if self.is_trailing else STRING.EMPTY
        return pattern

    @property
    def has_data(self):
        return len(self.lines) > NUMBER.ZERO

    @property
    def are_identical_lines(self):
        if not self.has_data:
            return False

        lst = [re.sub(PATTERN.WHITESPACES, STRING.EMPTY, line) for line in self.lines]
        return len(set(lst)) == NUMBER.ONE

    @property
    def is_diff(self):
        return self._is_diff

    @property
    def pattern(self):
        return self._pattern

    @property
    def snippet(self):
        return self._snippet

    def get_common_pattern(self):
        if not self.are_identical_lines:
            return STRING.EMPTY

        if len(set(self.lines)) == NUMBER.ONE:
            pattern = TextPattern(self.lines[INDEX.ZERO])
            return f"{self.leading_whitespace}{pattern}{self.trailing_whitespace}"

        lst_of_groups = list(zip(*[Text(line).do_finditer_split(r'\S+') for line in self.lines]))

        result = []
        for grp in lst_of_groups[INDEX.ONE:-INDEX.ONE]:
            if len(set(grp)) == 1:
                result.append(TextPattern(grp[INDEX.ZERO]))
            else:
                is_space_only = re.match(' +$', str.join('', grp))
                result.append(PATTERN.SPACES if is_space_only else PATTERN.WHITESPACES)
        pattern = str.join(STRING.EMPTY, result)
        return f"{self.leading_whitespace}{pattern}{self.trailing_whitespace}"

    def get_common_snippet(self):
        if not self.are_identical_lines:
            return STRING.EMPTY

        tbl = {' +': '(spaces)', ' *': '(space)',
               r'\s+': '(whitespaces)', r'\s*': '(whitespace)',
               '': STRING.EMPTY}
        case = tbl.get(self.leading_whitespace)
        leading_snippet = f"start({case})" if self.is_leading else STRING.EMPTY
        case = tbl.get(self.trailing_whitespace)
        trailing_snippet = f"end({case})" if self.is_trailing else STRING.EMPTY

        if len(set(self.lines)) == NUMBER.ONE:
            snippet = self.lines[INDEX.ZERO]
            snippet = f"{leading_snippet} {snippet} {trailing_snippet}".strip()
            return snippet

        lst_of_groups = list(zip(*[Text(line).do_finditer_split(r'\S+') for line in self.lines]))

        result = []
        for grp in lst_of_groups[INDEX.ONE:-INDEX.ONE]:
            if len(set(grp)) == 1:
                result.append(TextPattern(grp[INDEX.ZERO]))
            else:
                result.append(list(set(grp))[-INDEX.ONE])
        pattern = str.join(STRING.EMPTY, result)
        return f"{self.leading_whitespace}{pattern}{self.trailing_whitespace}"

    def process(self):
        if not self.has_data:
            return

        if self.are_identical_lines:
            self._pattern = self.get_common_pattern()
            self._snippet = self.get_common_snippet()
        else:
            node = DiffLinePattern(*self.lines, label=self.label)
            self._is_diff = node.is_diff
            self._pattern = node.pattern
            self._snippet = node.snippet

            if node.is_diff:
                tbl = {' +': 'spaces', ' *': 'space',
                       r'\s+': 'whitespaces', r'\s*': 'whitespace',
                       '': STRING.EMPTY}
                case = tbl.get(self.leading_whitespace)
                leading_snippet = f"start({case})" if self.is_leading else STRING.EMPTY
                case = tbl.get(self.trailing_whitespace)
                trailing_snippet = f"end({case})" if self.is_trailing else STRING.EMPTY
                self._pattern = f'{self.leading_whitespace}{self._pattern}{self.trailing_whitespace}'
                if leading_snippet:
                    self._snippet = self._snippet.replace('start()', leading_snippet)
                if trailing_snippet:
                    self._snippet = self._snippet.replace('end()', trailing_snippet)


class DText:
    def __init__(self, text):
        self.lst = []
        self.leading_lst = []
        self.trailing_lst = []
        self.text = text
        self.lst.append(text)
        leading = Misc.get_leading_line(text)
        leading and self.leading_lst.append(leading)
        trailing = Misc.get_trailing_line(text)
        trailing and self.trailing_lst.append(trailing)

    @property
    def leading(self):
        if not self.leading_lst:
            return STRING.EMPTY

        if len(set(self.leading_lst)) == NUMBER.ONE:
            return self.leading_lst[INDEX.ZERO]
        else:
            ws = STRING.SPACE_CHAR
            for item in self.leading_lst:
                if item.strip(STRING.SPACE_CHAR):
                    ws = item.strip(STRING.SPACE_CHAR)
                    break
            is_multi = any(len(item) > NUMBER.ONE for item in self.leading_lst)
            return f"{ws} " if is_multi else ws

    @property
    def trailing(self):
        if not self.trailing_lst:
            return STRING.EMPTY

        if len(set(self.trailing_lst)) == NUMBER.ONE:
            return self.trailing_lst[INDEX.ZERO]
        else:
            ws = STRING.SPACE_CHAR
            for item in self.trailing_lst:
                if item.strip(STRING.SPACE_CHAR):
                    ws = item.strip(STRING.SPACE_CHAR)
                    break
            is_multi = any(len(item) > NUMBER.ONE for item in self.trailing_lst)
            return f"{ws} " if is_multi else ws

    @property
    def first_text(self):
        first = self.lst[INDEX.ZERO] if self.lst else STRING.EMPTY
        return first

    @property
    def is_identical(self):
        return len(set(self.lst)) == NUMBER.ONE

    @property
    def is_closed_to_identical(self):
        clean_lst = [item.strip() for item in self.lst if item.strip()]
        return len(set(clean_lst)) == NUMBER.ONE

    def concatenate(self, text):
        if self.lst:
            self.lst[-INDEX.ONE] = self.lst[-INDEX.ONE] + text
        else:
            self.lst.append(text)

    def add(self, text):
        self.lst.append(text)

    def to_group(self):
        lst = []
        for line in self.lst:
            line = line.strip()
            if line:
                sub_lst = Text(line).do_finditer_split(PATTERN.WHITESPACES)
                lst.append(sub_lst)

        group = list(zip(*lst))
        for i, sub_grp in enumerate(group):
            group[i] = list(set(sub_grp))
        return group

    def to_general_text(self):
        result = []
        group = self.to_group()
        for sub_grp in group:
            if len(sub_grp) == NUMBER.ONE:
                result.append(sub_grp[INDEX.ZERO])
            else:
                ws = STRING.SPACE_CHAR
                for item in sub_grp:
                    if item.strip(STRING.SPACE_CHAR):
                        ws = item.strip(STRING.SPACE_CHAR)
                        break
                is_multi = any(len(item) > NUMBER.ONE for item in sub_grp)
                spacer = f"{ws} " if is_multi else ws
                result.append(spacer)
        general_text = self.leading + str.join(STRING.EMPTY, result) + self.trailing
        return general_text

    def get_pattern(self):
        if self.is_identical:
            return TextPattern(self.first_text)
        elif self.is_closed_to_identical:
            clean_lst = [item.strip() for item in self.lst if item.strip()]
            txt = clean_lst[INDEX.ZERO]
            pattern = TextPattern(self.leading + txt + self.trailing)
            return pattern
        else:
            return TextPattern(self.to_general_text())

    def get_snippet(self):
        if self.is_identical:
            return self.first_text
        elif self.is_closed_to_identical:
            clean_lst = [item.strip() for item in self.lst if item.strip()]
            txt = clean_lst[INDEX.ZERO]
            return self.leading + txt + self.trailing
        else:
            return self.to_general_text()


class DChange:
    def __init__(self, text, var):
        self.var = var
        self.lst = []
        self.text = text
        self.is_empty = text.strip() == STRING.EMPTY
        not self.is_empty and self.lst.append(text)

    def add(self, text):
        if text.strip() == STRING.EMPTY:
            self.is_empty = True
        not self.is_empty and text not in self.lst and self.lst.append(text)

    def get_pattern(self):
        snippet = self.get_snippet()
        pattern = ElementPattern(snippet)
        return pattern

    def get_snippet(self):
        factory = TranslatedPattern.do_factory_create(*self.lst)
        snippet = factory.get_template_snippet(var=self.var)
        snippet = '%s, or_empty)' % snippet[:-INDEX.ONE] if self.is_empty else snippet
        return snippet
