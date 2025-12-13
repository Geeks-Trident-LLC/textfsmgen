import re

from regexapp import TextPattern

from genericlib import STRING, NUMBER, PATTERN, SYMBOL, Misc
from genericlib.constpattern import get_ref_pattern_by_name
from textfsmgen.gp import RuntimeException, TranslatedPattern, LData


class SnippetElement(RuntimeException):
    def __init__(self, element_txt, trailing=''):
        self.element_txt = element_txt
        self.trailing = trailing
        self.name = STRING.EMPTY
        self.var_name = STRING.EMPTY
        self.value = STRING.EMPTY

        self.is_captured = False
        self.is_kept = False
        self.is_empty = False

        self.parse()

    def __call__(self, *args, **kwargs):
        new_instance = self.__class__(*args, **kwargs)
        return new_instance

    @property
    def var_index(self):
        pat = '[0-9]+(_[0-9]+)?$'
        match = re.search(pat, self.var_name)
        if match:
            matched_txt = match.group()
            if matched_txt.isdigit():
                result = int(matched_txt)
            else:
                first, last = str.split(matched_txt, STRING.UNDERSCORE_CHAR, maxsplit=1)
                result = int(first) * NUMBER.TEN + int(last)

            return result
        else:
            return NUMBER.ZERO

    def parse(self):
        pat = ('(?P<name>[a-zA-Z]+(_[a-zA-Z]+)*)[(] *'
               '(?P<check>[cCkK]?var)=(?P<var_name>.+), +'
               'value=(?P<value>.+) *[)]')
        match = re.match(pat, self.element_txt)
        if not match:
            self.raise_runtime_error(msg='Invalid element text\n%s' % self.element_txt)

        check = match.group('check')
        if check.lower() == 'cvar':
            self.is_captured = True
            self.is_empty = check == 'Cvar'
        elif check.lower() == 'kvar':
            self.is_kept = True
            self.is_empty = check == 'Kvar'

        self.name = match.group('name')
        self.var_name = match.group('var_name')
        self.value = match.group('value')

    def set_captured(self):
        self.is_captured = True
        self.is_kept = False

    def set_kept(self):
        self.is_captured = False
        self.is_kept = True

    def set_empty(self):
        self.is_empty = True

    def split(self, splitter='', ref_index=0):

        if splitter:
            pat = '[%s]+' % re.escape(splitter)
        else:
            pat = PATTERN.PUNCTS

        separators = re.findall(pat, self.value)
        items = re.split(pat, self.value)

        lst = []
        for index, item in enumerate(items):
            if index < len(items) - NUMBER.ONE:
                item and lst.append(item)
                lst.append(separators[index])
            else:
                item and lst.append(item)

        result = []
        for index, item in enumerate(lst):
            if ref_index:
                new_var_name = 'v%s' % (ref_index + index + 1)
            else:
                new_var_name = '%s%s' % (self.var_name, index)

            pat_obj = TranslatedPattern.do_factory_create(item)
            sub_editable_snippet = pat_obj.get_readable_snippet(var=new_var_name)

            trailing = self.trailing if index == len(lst) - NUMBER.ONE else STRING.EMPTY
            node = self(sub_editable_snippet, trailing=trailing)
            result.append(node)

        return result

    def join(self, *args):
        if args:
            txt = '%s%s' % (self.value, self.trailing)
            for arg in args:
                txt = '%s%s%s' % (txt, arg.value, arg.trailing)
            txt = txt.strip()
            actual_txt = txt.replace('_SYMBOL_LEFT_PARENTHESIS_', '(')
            actual_txt = actual_txt.replace('_SYMBOL_RIGHT_PARENTHESIS_', ')')
            new_pat_obj = TranslatedPattern.do_factory_create(actual_txt)
            element_txt = new_pat_obj.get_readable_snippet(var=self.var_name)
            trailing = arg.trailing     # noqa
        else:
            element_txt = self.element_txt
            trailing = self.trailing
        new_instance = self(element_txt, trailing=trailing)
        return new_instance

    def to_regex(self):
        if not self.is_kept and not self.is_captured:
            txt = f'{self.value}{self.trailing}'
            txt_pat = TextPattern(txt)
            return txt_pat
        else:
            pat = get_ref_pattern_by_name(self.name)

            if self.is_captured:
                if self.is_empty:
                    pat = f'(?P<{self.var_name}>({pat})|)'
                else:
                    pat = f'(?P<{self.var_name}>{pat})'
            else:
                if self.is_empty:
                    pat = f'(({pat})|)'

            if self.is_empty:
                if self.trailing:
                    is_space = bool(re.match(r' +$', self.trailing))
                    trailing_pat = ' *' if is_space else r'\s*'
                    pat = f'{pat}{trailing_pat}'
            else:
                pat = pat + TextPattern(self.trailing)
            return pat

    def to_template_snippet(self):

        if not self.is_kept and not self.is_captured:
            txt = f'{self.value}{self.trailing}'
            return txt
        else:
            if self.is_captured:
                if self.is_empty:
                    tmpl_snippet = f'{self.name}(var_{self.var_name}, or_empty)'
                else:
                    tmpl_snippet = f'{self.name}(var_{self.var_name})'
            else:
                tmpl_snippet = f'{self.name}(or_empty)' if self.is_empty else f'{self.name}()'

            if self.is_empty:
                if self.trailing:
                    is_space = bool(re.match(r' +$', self.trailing))
                    ws = 'zero_or_spaces()' if is_space else 'zero_or_whitespaces()'
                    tmpl_snippet = f'{tmpl_snippet}{ws}'
            else:
                tmpl_snippet = f"{tmpl_snippet}{self.trailing}"

            return tmpl_snippet

    def to_snippet(self):
        v = 'var'
        if self.is_captured or self.is_kept:
            v = 'cvar' if self.is_captured else 'kvar'
            v = v.title() if self.is_empty else v
        fmt = '%s(%s=%s, value=%s)'
        snippet = fmt % (self.name, v, self.var_name, self.value)
        snippet = snippet + self.trailing
        return snippet


class EditingSnippet(LData):
    def __init__(self, editing_snippet):    # noqa
        self.data = editing_snippet
        self.capture = STRING.EMPTY
        self.keep = STRING.EMPTY
        self.action = STRING.EMPTY
        self.raw_data = STRING.EMPTY
        self.snippet = STRING.EMPTY
        self.snippet_elements = []

        self.largest_index = 0

        self.is_action_applied = False
        self.is_keep_applied = False
        self.is_capture_applied = False

        self.process()

    def prepare(self):
        pat = (r'capture[(](?P<capture>[^\)]*)[)] '
               r'keep[(](?P<keep>[^\)]*)[)] '
               r'action[(](?P<action>[^\)]*)[)]: '
               r'(?P<snippet>.+)')

        match = re.match(pat, self.data)
        if not match:
            self.raise_runtime_error(msg='Invalid argument\n%s' % self.data)

        self.capture = match.group('capture').strip()
        self.keep = match.group('keep').strip()
        self.action = match.group('action').strip()
        self.raw_data = match.group('snippet')
        self.snippet = self.raw_data.strip()

        pat = r'\w+\([cCkK]?var=[^\)]+, value=[^\)]+\)'
        spacers = re.split(pat, self.snippet)[NUMBER.ONE:-NUMBER.ONE]
        items = re.findall(pat, self.snippet)
        total = len(items)

        for i, snippet_txt in enumerate(items):
            trailing = spacers[i] if i < total - NUMBER.ONE else STRING.EMPTY
            node = SnippetElement(snippet_txt, trailing=trailing)
            self.largest_index = max(self.largest_index, node.var_index)
            self.snippet_elements.append(node)

    def refresh_largest_index(self):
        for node in self.snippet_elements:
            self.largest_index = max(self.largest_index, node.var_index)

    def find_element(self, var_name):
        for index, node in enumerate(self.snippet_elements):
            if node.var_name == var_name:
                return index, node
        return -NUMBER.ZERO, None

    def apply_action_join(self, action_op):
        if not re.search('[_-]join', action_op, re.I):
            return False

        grp = re.split('[_-]join', action_op, re.I)[NUMBER.ZERO]

        if re.match(r'\d+:\d+$', grp):
            first, last = str.split(grp, STRING.COLON_CHAR, maxsplit=NUMBER.ONE)
            var_names = ['v%s' % i for i in range(int(first), int(last) + 1)]
            if not var_names:
                self.raise_runtime_error(
                    name='EditingSnippetActionJoinRTError',
                    msg='Invalid range (%s)' % action_op
                )
        elif re.match(r'\w+(,\w+)*', grp):
            var_names = ['v%s' % i if str.isdigit(i) else i for i in str.split(grp, STRING.COMMA_CHAR)]

        first_index, first_node = self.find_element(var_names[NUMBER.ZERO]) # noqa
        if first_index >= NUMBER.ZERO:
            remain_modes = []

            for var_name in var_names[NUMBER.ONE:]:
                index, node = self.find_element(var_name)
                if index >= NUMBER.ZERO:
                    remain_modes.append(node)
            joint_node = first_node.join(*remain_modes)
            self.snippet_elements[first_index] = joint_node
            self.is_action_applied = True

            for removed_node in remain_modes:
                removed_index = self.snippet_elements.index(removed_node)
                self.snippet_elements.pop(removed_index)
            self.refresh_largest_index()
            return True
        else:
            self.raise_runtime_error(
                name='EditingSnippetActionJoinRTError',
                msg='Not found index (%s)' % action_op
            )

    def apply_action_split(self, action_op):
        if not re.search('[_-]split', action_op, re.I):
            return False

        var_name, sep = re.split('[_-]split[-_]?', action_op, maxsplit=1, flags=re.I)
        sep = re.sub('_left_parenthesis_', SYMBOL.LEFT_PARENTHESIS, sep, flags=re.I)
        sep = re.sub('_right_parenthesis_', SYMBOL.RIGHT_PARENTHESIS, sep, flags=re.I)
        var_name = 'v%s' % var_name if var_name.isdigit() else var_name

        index, node = self.find_element(var_name)
        if index >= NUMBER.ZERO:
            self.refresh_largest_index()
            sub_lst = node.split(splitter=sep, ref_index=self.largest_index)
            left_sub_lst = self.snippet_elements[:index]
            right_sub_lst = self.snippet_elements[index + NUMBER.ONE:]
            self.snippet_elements = left_sub_lst + sub_lst + right_sub_lst
            self.is_action_applied = True
            self.refresh_largest_index()
        else:
            self.raise_runtime_error(
                name='EditingSnippetActionSplitRTError',
                msg='Not found index (%s)' % var_name
            )

    def apply_action(self):
        if not self.action:
            return

        action_ops = re.split(',? +', self.action)
        for action_op in action_ops:
            if not re.search('join|split', action_op, re.I):
                continue
            is_applied = self.apply_action_join(action_op)
            not is_applied and self.apply_action_split(action_op)

    def apply_keep(self):
        if not self.keep:
            return

        items = re.split(PATTERN.SPACES, self.keep)
        for item in items:
            item = item.strip(',')
            is_empty = bool(re.search('[_-]?or([_-]empty)?', item, re.I))
            item = re.sub('[_-]?or([_-]empty)?', STRING.EMPTY, item, re.I)

            if re.match(r'\d+:\d+$', item):
                first, last = str.split(item, STRING.COLON_CHAR, maxsplit=NUMBER.ONE)
                var_names = ['v%s' % i for i in range(int(first), int(last) + 1)]
                if not var_names:
                    self.raise_runtime_error(
                        name='EditingSnippetActionKeepRTError',
                        msg='Invalid range (%s)' % self.keep
                    )
            elif re.match(r'\w+(,\w+)*', item):
                var_names = ['v%s' % i if i.isdigit() else i for i in item.split(',')]

            for var_name in var_names:  # noqa
                index, node = self.find_element(var_name)
                if index >= NUMBER.ZERO:
                    node.set_kept()
                    is_empty and node.set_empty()
                    self.is_keep_applied = True
                else:
                    self.raise_runtime_error(
                        name='EditingSnippetActionKeepRTError',
                        msg='Not found index (%s)' % var_name
                    )

    def apply_capture(self):
        """
        Apply capture rules to variables defined in the capture string.

        This method parses the `self.capture` string into variable names,
        handles ranges (e.g., "1:3"), lists (e.g., "a,b,c"), and optional
        empty markers (e.g., "orEmpty"). It then marks the corresponding
        elements as captured and optionally empty.

        Steps
        -----
        1. Split the capture string by spaces.
        2. Normalize items by removing commas and replacing "orEmpty" markers.
        3. Expand ranges into sequential variable names (e.g., v1, v2, v3).
        4. Parse comma-separated identifiers into variable names.
        5. For each variable name, locate the element and mark it captured.

        Raises
        ------
        EditingSnippetActionCaptureRTError
            If a variable range is invalid or a variable cannot be found.

        Side Effects
        ------------
        - Sets `self.is_capture_applied` to True if any capture is applied.
        - Calls `node.set_captured()` and optionally `node.set_empty()` on
          matched elements.
        """
        if not self.capture:
            return

        items = re.split(PATTERN.SPACES, self.capture)
        for item in items:
            item = item.strip(',')
            is_empty = bool(re.search('[_-]?or([_-]empty)?', item, flags=re.I))
            item = re.sub('[_-]?or([_-]empty)?', STRING.EMPTY, item, flags=re.I)
            if re.match(r'\d+:\d+$', item):
                first, last = item.split(':', NUMBER.ONE)
                var_names = ['v%s' % i for i in range(int(first), int(last) + 1)]
                if not var_names:
                    self.raise_runtime_error(
                        name='EditingSnippetActionCaptureRTError',
                        msg='Invalid range (%s)' % self.capture
                    )
            elif re.match(r'\w+(,\w+)*', item):
                var_names = ['v%s' % i if i.isdigit() else i for i in item.split(',')]
            else:
                var_names = []

            for var_name in var_names:  # noqa
                index, node = self.find_element(var_name)
                if index >= NUMBER.ZERO:
                    node.set_captured()
                    is_empty and node.set_empty()
                    self.is_capture_applied = True
                else:
                    self.raise_runtime_error(
                        name='EditingSnippetActionCaptureRTError',
                        msg='Not found index (%s)' % var_name
                    )

    def process(self):
        self.prepare()
        if self.action:
            self.apply_action()
        else:
            self.apply_capture()
            self.apply_keep()

    def to_snippet(self):
        new_snippet = str.join(
            STRING.EMPTY, [elmt.to_snippet() for elmt in self.snippet_elements]
        )
        new_snippet = '%s%s%s' % (self.leading, new_snippet, self.trailing)

        cval = STRING.EMPTY if self.is_capture_applied else self.capture
        kval = STRING.EMPTY if self.is_keep_applied else self.keep
        aval = STRING.EMPTY if self.is_action_applied else self.action

        fmt = 'capture(%s) keep(%s) action(%s): %s'
        new_snippet = fmt % (cval, kval, aval, new_snippet)

        return new_snippet

    def to_regex(self):
        pattern = str.join(
            STRING.EMPTY, [elmt.to_regex() for elmt in self.snippet_elements]
        )
        if self.is_leading:
            pattern = '%s%s' % (PATTERN.ZOSPACES, pattern)

        if self.is_trailing:
            pattern = '%s%s' % (pattern, PATTERN.ZOSPACES)

        return pattern

    def to_template_snippet(self):
        tmpl_snippet = str.join(
            STRING.EMPTY, [elmt.to_template_snippet() for elmt in self.snippet_elements]
        )
        tmpl_snippet = f"{self.leading}{tmpl_snippet}{self.trailing}"
        # if self.is_leading:
        #     tmpl_snippet = '%s%s' % (self.leading, tmpl_snippet)
        #
        # if self.is_trailing:
        #     tmpl_snippet = '%s%s' % (tmpl_snippet, self.trailing)

        return tmpl_snippet


class IterativeLinePattern(LData):
    def __init__(self, line, label=''):
        super().__init__(line)
        pat = r'[\x20-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+'
        self.label = re.sub(pat, '_', str(label))
        self._snippet = STRING.EMPTY
        self.process()

    def __len__(self):
        chk = bool(len(self._snippet))
        return int(chk)

    def symbolize(self):
        spaces = re.findall(PATTERN.WHITESPACES, self.data)
        lst = []
        for index, item in enumerate(re.split(PATTERN.WHITESPACES, self.data)):
            node = TranslatedPattern.do_factory_create(item)
            var_ = 'v%s%s' % (self.label, index)

            item_snippet = node.get_readable_snippet(var=var_)
            lst.append(item_snippet)
            if index < len(spaces):
                lst.append(spaces[index])

        snippet = str.join(STRING.EMPTY, lst)
        fmt = 'capture() keep() action(): %s%s%s'
        editing_snippet = fmt % (self.leading, snippet, self.trailing)
        return editing_snippet

    def is_line_editable_snippet(self):
        pat = r'capture[(][^\)]*[)] keep[(][^\)]*[)] action[(][^\)]*[)]:.+'
        match = re.match(pat, self.data)
        chk = bool(match)
        return chk

    def process(self):
        if self.is_line_editable_snippet():
            node = EditingSnippet(self.data)
            self._snippet = node.to_snippet()
        else:
            self._snippet = self.symbolize()

    def to_snippet(self):
        node = EditingSnippet(self._snippet)
        snippet = node.to_snippet()
        return snippet

    def to_regex(self):
        node = EditingSnippet(self._snippet)
        pattern = node.to_regex()
        pattern = pattern.replace('_SYMBOL_LEFT_PARENTHESIS_', re.escape('('))
        pattern = pattern.replace('_SYMBOL_RIGHT_PARENTHESIS_', re.escape(')'))
        return pattern

    def to_template_snippet(self):
        node = EditingSnippet(self._snippet)
        tmpl_snippet = node.to_template_snippet()
        tmpl_snippet = tmpl_snippet.replace('_SYMBOL_LEFT_PARENTHESIS_', '(')
        tmpl_snippet = tmpl_snippet.replace('_SYMBOL_RIGHT_PARENTHESIS_', ')')
        return tmpl_snippet

    def is_captured_in_regex(self):
        data = self.to_regex()
        pat = r'[(][?]P<\w+>'
        chk = bool(re.search(pat, data))
        return chk

    def is_captured_in_template_snippet(self):
        data = self.to_template_snippet()
        pat = r'\b\w+[(][^\)]* *var_\w+'
        chk = bool(re.search(pat, data))
        return chk


class IterativeLinesPattern(RuntimeException):
    def __init__(self, *lines_or_snippets):
        self.lines_or_snippets = Misc.get_list_of_readonly_lines(*lines_or_snippets)

    def to_snippet(self):
        lst = []
        for index, line_or_snippet in enumerate(self.lines_or_snippets):
            if Misc.is_data_line(line_or_snippet):
                label = str(index) if index > 0 else STRING.EMPTY
                node = IterativeLinePattern(line_or_snippet, label=label)
                snippet = node.to_snippet()
                lst.append(snippet)
            else:
                lst.append(line_or_snippet)
        snippets = str.join('\n', lst)
        return snippets

    def to_regex(self):
        lst = []
        for snippet in self.lines_or_snippets:
            if Misc.is_data_line(snippet):
                node = IterativeLinePattern(snippet)
                pattern = node.to_regex()
                lst.append(pattern)
            else:
                lst.append(r'[ \t\v]*')

        if lst:
            pattern = str.join(r'(%s)' % PATTERN.CRNL, lst)
            return pattern
        else:
            return STRING.EMPTY

    def to_template_snippet(self):
        lst = []
        is_captured = False
        for snippet in self.lines_or_snippets:
            if Misc.is_data_line(snippet):
                node = IterativeLinePattern(snippet)
                tmpl_snippet = node.to_template_snippet()
                is_captured |= node.is_captured_in_template_snippet()
                lst.append(tmpl_snippet)

        if not is_captured:
            self.raise_runtime_error(
                msg='CANT form template snippet because no captured variable is created'
            )

        template_snippet = str.join(STRING.NEWLINE, lst)
        return template_snippet
