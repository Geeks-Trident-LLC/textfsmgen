from collections import Counter
import math
import statistics
import operator as op
import re

from regexapp import LinePattern

from genericlib import Misc, STRING, NUMBER, PATTERN, INDEX
from textfsmgen.gp import RuntimeException, TranslatedPattern

from textfsmgen.gpcommon import GPCommon


class TabularTextPattern(RuntimeException):
    def __init__(self, *lines, divider='', columns_count=0, col_widths=None,
                 header_names=None, headers_data=None, custom_headers_data='',
                 starting_from=None, ending_to=None,
                 is_headers_row=True):
        self.lines = Misc.get_list_of_lines(*lines)
        self.kwargs = dict(
            divider=divider,
            columns_count=columns_count,
            col_widths=col_widths or [],
            header_names=header_names,
            headers_data=headers_data,
            custom_headers_data=custom_headers_data,
            is_headers_row=is_headers_row
        )

        self.starting_from = starting_from
        self.ending_to = ending_to
        self.tabular_parser = None

        self.index_a = None
        self.index_b = None

        self.prepare_col_widths()
        self.process()

    def __len__(self):
        chk = bool(self.tabular_parser)
        return chk

    def prepare_col_widths(self):
        col_widths = self.kwargs.get('col_widths')
        if not col_widths:
            return

        fmt = 'Expecting list of integer or string of integers, but got %r'
        lst = []
        if Misc.is_string(col_widths) or Misc.is_list(col_widths):
            if Misc.is_string(col_widths):
                col_widths = str.strip(col_widths)
                widths = re.split(r'[ ,]+', col_widths.strip())
            else:
                widths = col_widths[:]

            for index, width_ in enumerate(widths):
                is_number, width = Misc.try_to_get_number(width_, return_type=int)
                if is_number:
                    lst.append(width)
                elif index == len(widths) - NUMBER.ONE:
                    lst.append(STRING.EMPTY)
                else:
                    self.raise_runtime_error(msg=fmt % col_widths)

            self.kwargs.update(col_widths=lst[:])
            self.kwargs.update(columns_count=len(lst))
        else:
            self.raise_runtime_error(msg=fmt % col_widths)

    def process(self):
        self.index_a = GPCommon.get_line_position_by(self.lines, self.starting_from)
        self.index_b = GPCommon.get_line_position_by(self.lines, self.ending_to)

        lines = self.lines[self.index_a:self.index_b]
        self.tabular_parser = TabularTextPatternByVarColumns(*lines, **self.kwargs)

    def to_regex(self):
        pattern = self.tabular_parser.to_regex() if self else STRING.EMPTY
        return pattern

    def to_template_snippet(self):
        tmpl_snippet = self.tabular_parser.to_template_snippet() if self else STRING.EMPTY

        if not tmpl_snippet.strip():
            return tmpl_snippet

        lines = tmpl_snippet.splitlines()
        first_line = lines[0]
        if self.index_a is not None:
            line_snippet = GPCommon.get_fixed_line_snippet(self.lines, index=self.index_a)
            if line_snippet:
                if re.search(LinePattern(line_snippet), first_line):
                    tmpl_snippet = Misc.join_string(*lines[1:], separator='\n')
                tmpl_snippet = f'{line_snippet} -> Table\nTable\n{tmpl_snippet}'

        lines = tmpl_snippet.splitlines()
        last_line = lines[-1]
        if self.index_b is not None:
            line_snippet = GPCommon.get_fixed_line_snippet(self.lines, index=self.index_b)
            if line_snippet:
                if re.search(LinePattern(line_snippet), last_line):
                    tmpl_snippet = Misc.join_string(*lines[:-1], separator='\n')
                tmpl_snippet = f'{tmpl_snippet}\n{line_snippet} -> EOF'

        return tmpl_snippet


class TabularTextPatternByVarColumns(RuntimeException):
    def __init__(self, *lines, divider='', columns_count=0, col_widths=None,
                 header_names=None, headers_data=None, custom_headers_data='',
                 is_headers_row=True, **kwargs):
        self._is_start_with_divider = None
        self._is_end_with_divider = None

        self.lines = Misc.get_list_of_lines(*lines)
        self.total_lines = len(self.lines)
        self.divider = divider
        self.col_widths = col_widths or []
        self.columns_count = columns_count
        self.raise_exception_if_columns_count_not_provided()
        self.headers_data = headers_data
        self.custom_headers_data = custom_headers_data
        self.raw_headers_data = []
        self.header_names = header_names
        self.is_headers_row = is_headers_row
        self.variables = []

        self.kwargs = kwargs

        self.prepare_headers_data()

    def __len__(self):
        return bool(self.columns_count)

    @property
    def is_divider_a_symbol(self):
        chk = bool(re.match(PATTERN.CHECK_PUNCT, self.divider))
        return chk

    @property
    def is_start_with_divider(self):
        if self._is_start_with_divider is None:
            if self.is_divider_a_symbol:
                count = 0
                for line in self.lines:
                    if line.strip().startswith(self.divider):
                        count += 1

                lines_count = len(self.lines)
                if count:
                    # chk = count > lines_count / NUMBER.TWO
                    chk = op.gt(count, op.truediv(lines_count, NUMBER.TWO))
                    self._is_start_with_divider = chk
                else:
                    self._is_start_with_divider = False
            else:
                self._is_start_with_divider = False
        return self._is_start_with_divider

    @property
    def is_end_with_divider(self):
        if self._is_end_with_divider is None:
            if self.is_divider_a_symbol:
                count = 0
                for line in self.lines:
                    if line.strip().endswith(self.divider):
                        count += 1

                lines_count = len(self.lines)
                if count:
                    # chk = count > lines_count / NUMBER.TWO
                    chk = op.gt(count, op.truediv(lines_count, NUMBER.TWO))
                    self._is_end_with_divider = chk
                else:
                    self._is_end_with_divider = False
            else:
                self._is_end_with_divider = False
        return self._is_end_with_divider

    def raise_exception_if_columns_count_not_provided(self):
        pat = f"{PATTERN.PUNCTS_GROUP}$"
        for line in self.lines:
            if re.match(pat, line.strip()):
                lst = re.split(PATTERN.WHITESPACES, line.strip())
                self.columns_count = len(lst)
                return
        if not self:
            self.raise_runtime_error(msg='columns_count CANT be zero')

    def prepare_headers_data(self):
        lst = self.raw_headers_data
        data = self.headers_data
        total_lines = len(self.lines)
        if Misc.is_string(data):
            pat = ' *[0-9]+([ ,]+[0-9]+)* *$'
            if re.match(pat, data):
                for index in re.split('[ ,]+', data):
                    index = int(index)
                    if index < total_lines:
                        hdr_line = self.lines[index]
                        hdr_line not in lst and lst.append(hdr_line)
            else:
                for sub_line in str.splitlines(data):
                    for line in self.lines:
                        sub_line in line and line not in lst and lst.append(line)

        elif Misc.is_list(data):
            for item in data:
                is_number, index = Misc.try_to_get_number(item, return_type=int)
                if is_number and index < total_lines:
                    hdr_line = self.lines[index]
                    hdr_line not in lst and lst.append(hdr_line)
                else:
                    for line in self.lines:
                        item in line and line not in lst and lst.append(line)

    def parse_headers_to_variables(self):
        variables = []
        header_names = self.header_names
        if not header_names:
            return variables

        if Misc.is_string(header_names):
            header_names = re.split('[ ,]+', header_names.strip())

        if Misc.is_list(header_names) and len(header_names) == self.columns_count:
            pat = '[ %s' % PATTERN.PUNCTS[1:]
            repl = STRING.UNDERSCORE_CHAR
            for i, hdr in enumerate(header_names):
                new_hdr = re.sub(pat, repl, hdr.strip())
                new_hdr = new_hdr if new_hdr == repl else new_hdr.rstrip(repl)
                if new_hdr in variables:
                    variables.append('%s%s' % (new_hdr, i))
                else:
                    variables.append(new_hdr)

        return variables

    def get_default_variables(self):  # noqa
        var_names = ['col%s' % i for i in range(self.columns_count)]
        return var_names

    def find_ref_row_by_symbols_divider(self, custom_line=''):
        fmt = ' *%(p)s( +%(p)s){%(rep)s} *$'
        repetition = self.columns_count - NUMBER.ONE
        pat = fmt % dict(p=PATTERN.PUNCTS, rep=repetition)

        if custom_line:
            found_line = custom_line
        else:
            found_lines = [line for line in self.lines if re.match(pat, line)]
            found_line = found_lines[NUMBER.ZERO] if found_lines else STRING.EMPTY
            if not found_line:
                return None

        pattern = ' *%s *' % PATTERN.PUNCTS
        ref_row = TabularRow.create_ref_row(
            found_line, pattern,
            case='findall',
            columns_count=self.columns_count
        )
        return ref_row

    def find_ref_row_by_separator_divider(self, custom_line=''):
        fmt = ' *%(sep)s?(%(p)s%(sep)s){%(rep)s}%(p)s%(sep)s? *$'
        kwargs = dict(
            p=r'[^%s]+' % self.divider,
            rep=self.columns_count - NUMBER.ONE,
            sep=re.escape(self.divider)
        )
        pat = fmt % kwargs

        if custom_line:
            found_line = custom_line
        else:
            found_lines = [line for line in self.lines if re.match(pat, line)]
            found_line = found_lines[NUMBER.ZERO] if found_lines else STRING.EMPTY
            if not found_line:
                return None

        ref_row = TabularRow.create_ref_row(
            found_line, self.divider,
            columns_count=self.columns_count,
            case='split'
        )
        return ref_row

    def find_ref_row_by_space_divider(self, spaces=' ', custom_line=''):
        gap = STRING.EMPTY if spaces == STRING.SPACE_CHAR else STRING.SPACE_CHAR
        repetition = self.columns_count - NUMBER.ONE
        kwargs = dict(
            p=PATTERN.NON_WHITESPACES_OR_PHRASE,
            rep=repetition, gap=gap
        )
        pat = ' *%(p)s(%(gap)s +%(p)s){%(rep)s} *$' % kwargs

        if custom_line:
            found_line = custom_line
        else:
            found_lines = [line for line in self.lines if re.match(pat, line)]
            if not found_lines:
                return None
            found_line = found_lines[NUMBER.ZERO]

        lst = []

        fmt1 = '(?P<%(key)s>%(p)s%(gap)s +)'
        fmt2 = '(?P<%(key)s> *%(p)s%(gap)s +)'
        fmt3 = '(?P<%(key)s>%(p)s *)$'

        for index in range(self.columns_count):
            key = 'v%03d' % index
            kwargs.update(key=key)
            fmt = fmt1 if index else fmt2
            lst.append(fmt % kwargs)
        else:
            lst[-NUMBER.ONE] = fmt3 % kwargs

        pattern = str.join(STRING.EMPTY, lst)

        ref_row = TabularRow.create_ref_row(
            found_line, pattern,
            columns_count=self.columns_count,
            case='variable'
        )
        return ref_row

    def find_ref_row_by_blank_space_divider(self):
        ref_row = self.find_ref_row_by_space_divider()
        return ref_row

    def find_ref_row_by_multi_spaces_divider(self):
        ref_row = self.find_ref_row_by_space_divider(spaces='  ')
        return ref_row

    def find_ref_row_by_custom_headers_line(self):
        ref_row = self.find_ref_row_by_symbols_divider(custom_line=self.custom_headers_data)
        return ref_row

    def find_ref_row_by_col_widths(self, custom_line=''):
        lst = []
        for index, width in enumerate(self.col_widths):
            if index < self.columns_count - NUMBER.ONE:
                lst.append('(?P<v%03d>.{%s})' % (index, width))
            else:
                lst.append('(?P<v%03d>.*)' % index)

        pattern = Misc.join_string(*lst)

        if custom_line:
            found_line = custom_line
        else:
            found_lines = [line for line in self.lines if re.match(pattern, line)]
            if not found_lines:
                return None
            found_line = found_lines[NUMBER.ZERO]
        ref_row = TabularRow.create_ref_row(
            found_line, pattern,
            columns_count=self.columns_count,
            case='variable'
        )
        return ref_row

    def try_to_get_table_by(self, case):
        methods = dict(
            col_widths=self.find_ref_row_by_col_widths,
            symbols=self.find_ref_row_by_symbols_divider,
            separator=self.find_ref_row_by_separator_divider,
            multi_spaces=self.find_ref_row_by_multi_spaces_divider,
            blank_space=self.find_ref_row_by_blank_space_divider,
            custom=self.find_ref_row_by_custom_headers_line
        )
        default_method = self.find_ref_row_by_blank_space_divider
        ref_row = methods.get(case, default_method)()
        if ref_row:
            header_names = self.parse_headers_to_variables()
            table = TabularTable(
                *self.lines, ref_row=ref_row, divider=self.divider,
                header_names=header_names,
                raw_headers_data=self.raw_headers_data,
                is_start_with_divider=self.is_start_with_divider,
                is_end_with_divider=self.is_end_with_divider,
                is_headers_row=self.is_headers_row
            )
            return True, table
        else:
            return False, None

    def parse_table(self):
        case, err_msg = STRING.EMPTY, STRING.EMPTY
        if self.col_widths:
            case = 'col_widths'
            err_msg = 'Failed to parse tabular text by column widths'
        elif re.match('%s$' % PATTERN.PUNCT, self.divider.strip()):
            case = 'separator'
            err_msg = 'Failed to parse tabular text by %r divider' % self.divider
        elif self.custom_headers_data:
            case = 'custom'
            err_msg = 'Failed to parse tabular text by custom headers data'
        elif self.divider == STRING.SPACE_CHAR:
            case = 'blank_space'
            err_msg = 'Failed to parse tabular text by blank space divider'
        elif re.match('  +$', self.divider):
            case = 'multi_spaces'
            err_msg = 'Failed to parse tabular text by multi-space divider'
        elif self.divider == STRING.EMPTY:
            case = 'symbols'
            err_msg = 'Failed to parse tabular text by symbols divider'
        else:
            msg = 'Unsupported divider %r' % self.divider
            self.raise_runtime_error(msg=msg)

        is_parsed, table = self.try_to_get_table_by(case)
        if is_parsed:
            return table
        else:
            self.raise_runtime_error(msg=err_msg)

    def to_regex(self):
        table = self.parse_table()
        if not table:
            msg = ('CANT build regex pattern because provided '
                   'text might not be tabular text format')
            self.raise_runtime_error(msg=msg)
        pattern = table.to_regex()
        return pattern

    def to_template_snippet(self):
        table = self.parse_table()
        if not table:
            msg = ('CANT build template snippet because provided '
                   'text might not be tabular text format')
            self.raise_runtime_error(msg=msg)
        template_snippet = table.to_template_snippet()
        return template_snippet


class TabularTable(RuntimeException):
    def __init__(self, *lines, ref_row=None, divider='', col_widths=None,
                 header_names=None, raw_headers_data=None,
                 is_start_with_divider=False, is_end_with_divider=False,
                 is_headers_row=True):
        self.first_column_data_info = dict()
        self.last_column_data_info = dict()

        self.lines = self.prepare_lines(lines)
        self.ref_row = ref_row
        self.divider = divider
        self.col_widths = col_widths

        self.rows = []
        self.columns = []
        self.header_lines = []
        self.header_columns = []
        self.header_names = header_names or []
        self.raw_headers_data = raw_headers_data or []

        self._is_leading = None
        self._is_trailing = None

        self.is_start_with_divider = is_start_with_divider
        self.is_end_with_divider = is_end_with_divider
        self.is_headers_row = is_headers_row

        self.is_divider = bool(self.divider.strip())
        self.divider_snippet = 'zero_or_spaces()%szero_or_spaces()' % re.escape(self.divider)
        self.divider_leading_snippet = '%szero_or_spaces()' % re.escape(self.divider)
        self.divider_trailing_snippet = 'zero_or_spaces()%s' % re.escape(self.divider)

        self.process()

    def __len__(self):
        chk = bool(self.rows) and bool(self.columns)
        return chk

    def __repr__(self):
        fmt = '%s(rows_count=%s, columns_count=%s)'
        cls_name = Misc.get_instance_class_name(self)
        result = fmt % (cls_name, len(self.rows), len(self.columns))
        return result

    @property
    def is_leading(self):
        if self._is_leading is None:
            if self._is_leading is None:
                lst = []
                for cell in self.first_column.cells:
                    if cell.text.strip():
                        lst.append(Misc.is_leading_line(cell.data))
                for key in self.first_column_data_info:
                    if isinstance(key, int):
                        data = self.first_column_data_info.get(key)
                        lst.append(Misc.is_leading_line(data))

                self._is_leading = any(lst)
        return self._is_leading

    @property
    def is_trailing(self):
        if self._is_trailing is None:
            for line in self.lines:
                self._is_trailing = Misc.is_trailing_line(line)
                if self._is_trailing:
                    break
        return self._is_trailing

    @property
    def rows_count(self):
        total = len(self.rows)
        return total

    @property
    def columns_count(self):
        total = len(self.columns)
        return total

    @property
    def first_column(self):
        first_col = self.columns[INDEX.ZERO]
        return first_col

    @property
    def last_column(self):
        last_col = self.columns[-INDEX.ONE]
        return last_col

    def prepare_lines(self, lines):
        pattern = r'^ *< *user[ ._+-]marker[ ._+-](?P<case>one|multi)[ ._+-]?line *>'

        lst = []
        is_continue = False
        all_lines = Misc.get_list_of_lines(*lines)
        total_lines = len(all_lines)
        baseline_spacers_count = None
        index = 0
        while index < total_lines:
            line = all_lines[index]
            if is_continue:
                if baseline_spacers_count is None:
                    baseline_spacers_count = len(Misc.get_leading_line(line))
                    lst_data = self.last_column_data_info.get('lst_data', [])
                    self.last_column_data_info.update(lst_data=lst_data)
                    lst_data.append(line.lstrip())
                    spacers = self.last_column_data_info.get('spacers', [])
                    self.last_column_data_info.update(spacers=spacers)
                    if not spacers:
                        left_spacer = baseline_spacers_count - 6
                        spacers.append(2 if left_spacer <= 0 else left_spacer)
                        spacers.append(baseline_spacers_count)
                    else:
                        left_spacer = min(spacers[0], baseline_spacers_count - 6)
                        spacers[0] = 2 if left_spacer <= 0 else left_spacer
                        spacers[1] = max(spacers[1], baseline_spacers_count)
                    index += 1
                    continue
                else:
                    spacers_count = len(Misc.get_leading_line(line))
                    if spacers_count > .8 * baseline_spacers_count:
                        lst_data = self.last_column_data_info.get('lst_data', [])
                        self.last_column_data_info.update(lst_data=lst_data)
                        lst_data.append(line.lstrip())
                        spacers = self.last_column_data_info.get('spacers', [])
                        self.last_column_data_info.update(spacers=spacers)
                        if not spacers:
                            left_spacer = spacers_count - 6
                            spacers.append(2 if left_spacer <= 0 else left_spacer)
                            spacers.append(baseline_spacers_count)
                        else:
                            left_spacer = min(spacers[0], spacers_count - 6)
                            spacers[0] = 2 if left_spacer <= 0 else left_spacer
                            spacers[1] = max(spacers[1], spacers_count)
                        index += 1
                        continue
                    else:
                        is_continue = False
                        baseline_spacers_count = None

            match = re.match(pattern, line)
            if match:
                is_oneline = match.group('case').lower() == 'one'
                if is_oneline:
                    first_col_data = re.sub(pattern, '', line)
                    next_line = re.sub(pattern, '', all_lines[index + NUMBER.ONE])
                    leading = Misc.get_leading_line(next_line)
                    self.first_column_data_info[len(lst)] = first_col_data
                    self.first_column_data_info.update(spacers_count=len(leading))
                    indices = self.first_column_data_info.get('indices', [])
                    self.first_column_data_info.update(indices=indices)
                    indices.append(next_line)
                    lst.append(next_line)
                    index += 1
                else:
                    indices = self.last_column_data_info.get('indices', [])
                    self.last_column_data_info.update(indices=indices)

                    new_line = re.sub(pattern, '', line)
                    indices.append(new_line)
                    lst.append(new_line)
                    is_continue = True
            else:
                lst.append(line)

            index += 1

        return lst

    def add_data_to_rows(self):
        self.rows.clear()
        for index, line in enumerate(self.lines):
            row = TabularRow(line, ref_row=self.ref_row)
            if index in self.first_column_data_info:
                first_cell = row.cells[0]
                first_cell.set_data(self.first_column_data_info.get(index))
            self.rows.append(row)

    def add_data_to_columns(self):
        self.columns.clear()
        is_created = False

        for row in self.rows:
            prev_column = None
            for index, cell in enumerate(row.cells):
                new_col = TabularColumn(index=index)
                column = self.columns[index] if is_created else new_col
                not is_created and self.columns.append(column)
                column.left_column = prev_column
                column.append_cell(cell)

                if prev_column:
                    prev_column.right_column = column

                prev_column = column
            is_created = True
        for col in self.columns:
            col.analyze_and_update_alignment()

        last_column = self.columns[-INDEX.ONE]
        last_column.add_extra_data(self.last_column_data_info.get('lst_data'))

    def to_list_of_dict(self):
        lst_of_dict = []
        divider = self.divider
        for row_index, row in enumerate(self.rows):
            if row.is_group_of_symbols:
                continue
            dict_obj = dict()
            lst_of_dict.append(dict_obj)
            for col in self.columns:
                txt = col.cells[row_index].data.strip()
                txt = txt.strip(divider).strip() if divider else txt
                dict_obj[col.name] = txt
        return lst_of_dict

    def do_cleaning_data(self):
        if not self.ref_row:
            return

        if self.is_headers_row:
            ref_line = self.ref_row.line
            if ref_line in self.lines:
                row_pos = self.lines.index(ref_line)
                self.rows = self.rows[row_pos + NUMBER.ONE:]
                self.header_lines = self.lines[:row_pos + NUMBER.ONE]
                for col in self.columns:
                    hdr_col = TabularColumn()
                    hdr_col.cells = col.cells[:row_pos + NUMBER.ONE]
                    self.header_columns.append(hdr_col)
                    col.cells = col.cells[row_pos + NUMBER.ONE:]

    def build_and_update_headers(self):
        if self.is_headers_row:
            if not self.header_names:
                repl_char = STRING.UNDERSCORE_CHAR
                pat = r'[0-9 \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+'
                for index, hdr_col in enumerate(self.header_columns):
                    col_name = str.join(repl_char, [cell.text for cell in hdr_col.cells])
                    col_name = re.sub(pat, repl_char, col_name)
                    col_name = col_name.strip(repl_char).lower()
                    col_name = col_name or 'col%s' % index
                    if col_name in self.header_names:
                        col_name = '%s%s' % (col_name, index)
                    self.header_names.append(col_name)
                    self.columns[index].name = col_name
        else:
            if self.header_names and len(self.header_names) == self.columns_count:
                for index, col_name in enumerate(self.header_names):
                    self.columns[index].name = col_name

    def process(self):
        self.add_data_to_rows()
        self.add_data_to_columns()
        self.do_cleaning_data()
        self.build_and_update_headers()

    def to_regex(self):
        if not self:
            return STRING.EMPTY

        lst = []
        does_prev_col_has_empty_cell = False
        divider_pat = ' *%s *' % re.escape(self.divider)
        divider_leading_pat = '%s *' % re.escape(self.divider)
        divider_trailing_pat = ' *%s' % re.escape(self.divider)
        for column in self.columns:
            has_empty_cell = does_prev_col_has_empty_cell or column.has_empty_cell
            if self.is_divider:
                lst and lst.append(divider_pat)
            else:
                sep_pat = PATTERN.SPACE if has_empty_cell else PATTERN.SPACES
                lst and lst.append(sep_pat)
            col_pat = column.to_regex()
            lst.append(col_pat)
            does_prev_col_has_empty_cell = column.has_empty_cell

        self.is_start_with_divider and lst.insert(NUMBER.ZERO, divider_leading_pat)
        if self.is_leading:
            lst.insert(NUMBER.ZERO, PATTERN.ZOSPACES)
        self.is_end_with_divider and lst.append(divider_trailing_pat)
        if self._is_trailing:
            lst.append(PATTERN.ZOSPACES)
        pattern = Misc.join_string(*lst)
        return pattern

    def get_header_lines_snippet(self):
        headers_lines = self.raw_headers_data if self.raw_headers_data else self.header_lines

        lst = []
        for line in Misc.get_list_of_lines(*headers_lines):
            is_line_of_symbols = bool(re.match(PATTERN.CHECK_PUNCTS_GROUP, line))
            is_header_line = Misc.is_data_line(line) and not is_line_of_symbols
            is_header_line and lst.append(line)

        snippet = Misc.join_string(*lst, sep=STRING.NEWLINE)
        return snippet

    def to_template_snippet(self):
        if not self:
            return STRING.EMPTY

        lst_of_snippet = []
        headers_snippet = self.get_header_lines_snippet()
        self.is_headers_row and headers_snippet and lst_of_snippet.append(headers_snippet)
        self.build_snippet_for_last_column_case(lst_of_snippet)
        self.build_snippet_for_first_column_case(lst_of_snippet)
        self.build_snippet_for_other_case(lst_of_snippet)
        template_snippet = Misc.join_string(*lst_of_snippet, sep=STRING.NEWLINE)

        return template_snippet

    def build_snippet_for_first_column_case(self, lst_of_snippet):
        if not self.first_column_data_info:
            return

        leading_snippet = 'start(space)' if self.is_leading else 'start()'
        trailing_snippet = 'end(space) -> record' if self.is_trailing else 'end() -> record'

        first_snippet = self.first_column.to_template_snippet(skipped_empty=True)
        first_snippet = f'{leading_snippet} {first_snippet} end(space) -> Next'

        indices = self.first_column_data_info.get('indices', [])
        layouts = []
        for row in self.rows:
            if row.line in indices:
                row.row_layout not in layouts and layouts.append(row.row_layout)

        for layout in sorted(layouts, reverse=True):
            lst = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width
                if m == n:
                    m = n - 4 if (n - 4) > 2 else abs(n - 2)
                space_snippet = f'space(repetition_{m}_{n})'
                kwargs = dict()
                if self.last_column_data_info and index == self.columns_count - NUMBER.ONE:
                    kwargs.update(added_list_meta_data=True)

                col_snippet = column.to_template_snippet(**kwargs)
                lst.append(col_snippet if int(bit) else space_snippet)

            sep = self.divider_snippet if self.is_divider else STRING.DOUBLE_SPACES
            next_snippet = Misc.join_string(*lst, sep=sep)
            if self.is_divider:
                next_snippet = f'{self.divider_leading_snippet}{next_snippet}{self.divider_trailing_snippet}'
                next_snippet = f'start() {next_snippet} {trailing_snippet}'
            else:
                pat = r' +space[(]repetition_\d+_\d+[)] *$'
                if re.search(pat, next_snippet):
                    next_snippet = re.sub(pat, ' end(space)', next_snippet)
                else:
                    next_snippet = f'{next_snippet} {trailing_snippet}'

                pat = r' *space[(]repetition_\d+_\d+[)] *'
                if re.match(pat, next_snippet):
                    next_snippet = f'start() {next_snippet}'
                else:
                    next_snippet = f'{leading_snippet} {next_snippet}'

            pat = r' +(space[(]repetition_\d+_\d+[)]) +'
            next_snippet = re.sub(pat, r' \1 ', next_snippet)

            lst_of_snippet.append(first_snippet)
            lst_of_snippet.append(next_snippet)

    def build_snippet_for_last_column_case(self, lst_of_snippet):
        if not self.last_column_data_info:
            return

        leading_snippet = 'start(space)' if self.is_leading else 'start()'

        first_snippet = self.first_column.to_template_snippet(to_bared_snippet=True)
        if self.is_divider:
            first_snippet = f'{self.divider_leading_snippet}{first_snippet}'
        lst_of_snippet.append(f'{leading_snippet} {first_snippet}zero_or_spaces() -> continue.record')

        indices = self.last_column_data_info.get('indices', [])
        layouts = []
        for row in self.rows:
            if row.line in indices:
                row.row_layout not in layouts and layouts.append(row.row_layout)

        for layout in sorted(layouts, reverse=True):
            lst = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width
                if m == n:
                    m = n - 4 if (n - 4) > 2 else abs(n - 2)
                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = dict()
                if index == self.columns_count - NUMBER.ONE:
                    kwargs.update(added_list_meta_data=True)
                col_snippet = column.to_template_snippet(**kwargs)

                if int(bit) or self.is_divider:
                    lst.append(col_snippet if int(bit) else space_snippet)
                else:
                    if lst:
                        last_item = lst[-INDEX.ONE]
                        pat = r'space[(]repetition_(?P<m>\d+)_(?P<n>\d+)[)]$'
                        match = re.match(pat, last_item)
                        if match:
                            m, n = int(match.group('m')), int(match.group('n'))
                            m += column.width
                            n += column.max_width - column.max_edge_leading_width
                            if m == n:
                                m = n - 4 if (n - 4) > 2 else abs(n - 2)
                            extend_space_snippet = f'space(repetition_{m}_{n})'
                            lst.pop()
                            lst.append(extend_space_snippet)
                        else:
                            lst.append(space_snippet)
                    else:
                        lst.append(space_snippet)

            sep = self.divider_snippet if self.is_divider else STRING.DOUBLE_SPACES
            line_snippet = Misc.join_string(*lst, sep=sep)
            if self.is_divider:
                line_snippet = f'{self.divider_leading_snippet}{line_snippet}{self.divider_trailing_snippet}'

            pat = r' *space[(]repetition_\d+_\d+[)] *$'
            if re.search(pat, line_snippet):
                line_snippet = re.sub(pat, ' end(space) -> continue', line_snippet)
            else:
                line_snippet = f'{line_snippet} end(space) -> continue'

            pat = r' *space[(]repetition_\d+_\d+[)] *'
            if re.match(pat, line_snippet):
                line_snippet = f'start() {line_snippet}'
            else:
                line_snippet = f'{leading_snippet} {line_snippet}'

            pat = r' +(space[(]repetition_\d+_\d+[)]) +'
            line_snippet = re.sub(pat, r' \1 ', line_snippet)
            lst_of_snippet.append(line_snippet)

        last_snippet = self.last_column.to_template_snippet(skipped_empty=True, added_list_meta_data=True)
        m, n = self.last_column_data_info.get('spacers')
        m = n - 4 if (n - 4) > 0 else m
        spacer_snippet = f'start() space(repetition_{m}_{n+2}) {last_snippet} end(space) -> continue'
        lst_of_snippet.append(spacer_snippet)

    def build_snippet_for_other_case(self, lst_of_snippet):

        leading_snippet = 'start(space)' if self.is_leading else 'start()'
        trailing_snippet = 'end(space) -> record' if self.is_trailing else 'end() -> record'

        a_indices = self.first_column_data_info.get('indices', [])
        b_indices = self.last_column_data_info.get('indices', [])
        layouts = []
        for row in self.rows:
            if row.line in a_indices or row.line in b_indices:
                continue
            row.row_layout not in layouts and layouts.append(row.row_layout)

        for layout in sorted(layouts, reverse=True):
            lst = []
            for index, bit in enumerate(list(layout)):
                column = self.columns[index]
                m, n = column.width, column.max_width
                m = n - 2 if m == n and m > 1 else m
                space_snippet = f'space(repetition_{m}_{n})'

                kwargs = dict()
                if self.last_column_data_info and index == self.columns_count - NUMBER.ONE:
                    kwargs.update(added_list_meta_data=True)
                col_snippet = column.to_template_snippet(**kwargs)

                if int(bit) or self.is_divider:
                    lst.append(col_snippet if int(bit) else space_snippet)
                else:
                    if lst:
                        last_item = lst[-INDEX.ONE]
                        pat = r'space[(]repetition_(?P<m>\d+)_(?P<n>\d+)[)]$'
                        match = re.match(pat, last_item)
                        if match:
                            m, n = int(match.group('m')), int(match.group('n'))
                            m += column.width
                            n += column.max_width - column.max_edge_leading_width
                            extend_space_snippet = f'space(repetition_{m}_{n})'
                            lst.pop()
                            lst.append(extend_space_snippet)
                        else:
                            lst.append(space_snippet)
                    else:
                        lst.append(space_snippet)

            sep = self.divider_snippet if self.is_divider else STRING.DOUBLE_SPACES
            line_snippet = Misc.join_string(*lst, sep=sep)
            if self.is_divider:
                line_snippet = f'{self.divider_leading_snippet}{line_snippet}{self.divider_trailing_snippet}'

            pat = r' *space[(]repetition_\d+_\d+[)] *$'
            if re.search(pat, line_snippet):
                line_snippet = re.sub(pat, ' end(space) -> record', line_snippet)
            else:
                line_snippet = f'{line_snippet} {trailing_snippet}'

            pat = r' *space[(]repetition_\d+_\d+[)] *'
            if re.match(pat, line_snippet):
                line_snippet = f'start() {line_snippet}'
            else:
                line_snippet = f'{leading_snippet} {line_snippet}'

            pat = r' +(space[(]repetition_\d+_\d+[)]) +'
            line_snippet = re.sub(pat, r' \1 ', line_snippet)

            is_line_snippet_existed = False
            pattern = r'(?i) *start\(\w*\) *(?P<chk>.+) *end\(\w*\) -> (record|continue)'
            match = re.match(pattern, line_snippet)
            if match:
                baseline_chk = match.group('chk')
                for snippet_ in lst_of_snippet:
                    if is_line_snippet_existed:
                        break
                    other_match = re.match(pattern, snippet_)
                    if other_match:
                        is_line_snippet_existed = other_match.group('chk') == baseline_chk
            not is_line_snippet_existed and lst_of_snippet.append(line_snippet)


class TabularCell(RuntimeException):
    def __init__(self, line, left_pos, right_pos, ref_cell=None):
        self.args = (line, left_pos, right_pos, ref_cell)

        self._leading = None
        self._trailing = None

        self.left = NUMBER.ZERO
        self.right = NUMBER.ZERO
        self.inner_left = NUMBER.ZERO
        self.inner_right = NUMBER.ZERO

        self.line = STRING.EMPTY
        self.data = STRING.EMPTY

        self.ref_cell = None

        self.process()

    def __len__(self):
        chk = self.left >= NUMBER.ZERO
        chk = chk and self.right > self.left
        return chk

    def __repr__(self):
        fmt = '%s(text=%r, data=%r, left=%s, right=%s)'
        cls_name = Misc.get_instance_class_name(self)
        result = fmt % (cls_name, self.text, self.data, self.left, self.right)
        return result

    @property
    def text(self):
        return self.data.strip()

    @property
    def leading(self):
        if self._leading is None:
            leading_spaces = Misc.get_leading_line(self.data)
            self._leading = leading_spaces
        return self._leading or STRING.EMPTY

    @property
    def trailing(self):
        if self._trailing is None:
            if self.is_empty:
                self._trailing = STRING.EMPTY
            else:
                lst = re.findall(PATTERN.SPACESATEOS, self.data)
                self._trailing = lst[NUMBER.ZERO] if lst else STRING.EMPTY
        return self._trailing or STRING.EMPTY

    @property
    def is_leading(self):
        chk = self.leading != STRING.EMPTY
        return chk

    @property
    def is_single_leading(self):
        chk = self.leading == STRING.SPACE_CHAR
        return chk

    @property
    def is_multi_leading(self):
        chk = len(self.leading) > NUMBER.ONE
        return chk

    @property
    def is_trailing(self):
        chk = self.trailing != STRING.EMPTY
        return chk

    @property
    def is_single_trailing(self):
        chk = self.trailing == STRING.SPACE_CHAR
        return chk

    @property
    def is_multi_trailing(self):
        chk = len(self.trailing) > NUMBER.ONE
        return chk

    @property
    def is_empty(self):
        chk = self.text == STRING.EMPTY
        return chk

    @property
    def is_just_chars(self):
        if self.is_empty:
            return False
        chk = STRING.SPACE_CHAR not in self.text
        return chk

    @property
    def is_group_of_chars(self):
        if self.is_empty:
            return False
        chk = STRING.SPACE_CHAR in self.text
        return chk

    @property
    def is_not_containing_space(self):
        chk = STRING.SPACE_CHAR not in self.text
        return chk

    @property
    def is_containing_space(self):
        chk = STRING.SPACE_CHAR in self.text
        return chk

    @property
    def items_count(self):
        if self.is_empty:
            return NUMBER.ZERO
        else:
            lst = re.split(PATTERN.SPACES, self.text)
            count = len(lst)
            return count

    @property
    def width(self):
        base_width = self.right - self.left
        width = len(self.data)
        if base_width > 0:
            return width if width < base_width else base_width
        else:
            return width

    @property
    def is_containing_spaces(self):
        chk = STRING.DOUBLE_SPACES in self.text
        return chk

    def update_position(self, attr, val=0):
        attr = 'left' if attr.lower() == 'left' else 'right'
        setattr(self, attr, val)
        self.process()

    def get_possible_prefix(self):
        if self.is_empty or self.is_trailing:
            return STRING.EMPTY
        else:
            *chk, prefix = self.text.rsplit(STRING.SPACE_CHAR, maxsplit=NUMBER.ONE)
            return STRING.EMPTY if chk else prefix

    def get_postfix_data(self):
        if self.is_multi_trailing or not self.is_containing_space:
            return STRING.EMPTY

        spaces = STRING.DOUBLE_SPACES
        space = STRING.SPACE_CHAR
        repl = spaces if self.is_containing_spaces else space
        _, remaining_txt = str.rsplit(self.text, repl, maxsplit=NUMBER.ONE)
        ret_val = Misc.join_string(remaining_txt, self.trailing)

        if self.ref_cell:
            other_right = self.right - len(ret_val)
            if other_right > self.ref_cell.inner_right:
                return ret_val
            else:
                if space in remaining_txt:
                    _, remaining_txt1 = str.rsplit(remaining_txt, space, maxsplit=NUMBER.ONE)
                    ret_val = Misc.join_string(remaining_txt1, self.trailing)
                    return ret_val
                else:
                    return STRING.EMPTY
        else:
            return ret_val

    def do_first_pass_adjustment(self, prev_cell=None):
        if not isinstance(prev_cell, self.__class__):
            # skip adjustment
            return

        prefix = prev_cell.get_possible_prefix()
        prefix_length = len(prefix)
        if not self.is_leading and prefix:
            self.left = self.left - prefix_length
            prev_cell.right = prev_cell.right - prefix_length
            self.process()
            prev_cell.process()

    def readjust(self, prev_cell=None):
        if not isinstance(prev_cell, self.__class__):
            # skip adjustment
            return

        chk1 = prev_cell.is_multi_trailing
        chk2 = prev_cell.is_empty
        chk3 = prev_cell.is_single_trailing and self.is_leading

        if chk1 or chk2 and chk3:
            # skip adjustment
            return
        else:
            prefix = prev_cell.get_postfix_data()
            if prefix:
                width = len(prefix) + NUMBER.ONE
                self.update_position('left', val=self.left-width)
                prev_cell.update_position('right', val=self.right-width)
            else:
                # skip adjustment
                return

    def process(self):
        line, left_pos, right_pos, ref_cell = self.args

        is_left, left = Misc.try_to_get_number(left_pos, return_type=int)
        is_right, right = Misc.try_to_get_number(right_pos, return_type=int)

        not is_left and self.raise_runtime_error(msg='left position must be integer')
        not is_right and self.raise_runtime_error(msg='right position must be integer')

        self._leading = None
        self._trailing = None

        if isinstance(ref_cell, self.__class__) or ref_cell is None:
            self.ref_cell = ref_cell
        else:
            cls_name = Misc.get_instance_class_name(self)
            self.raise_runtime_error(msg='invalid ref_cell type (%s)' % cls_name)

        self.left = left
        self.right = len(line) if self.ref_cell and right == 999999 else right
        self.line = line
        self.data = self.line[self.left:self.right]

        self.inner_left = self.left + len(self.leading)
        self.inner_right = self.right - len(self.trailing)

    def set_data(self, data):
        self.data = data
        self._leading = None
        self._trailing = None


class TabularRow(RuntimeException):
    def __init__(self, line, ref_row=None, aligned=True):
        self._is_symbols_group = None
        self.aligned = aligned
        self.line = line
        self.ref_row = ref_row
        self.row_layout = ''
        self.cells = []
        self.process()

    def __len__(self):
        chk = bool(self.cells)
        return chk

    def __repr__(self):
        fmt = '%s(columns_count=%s)'
        cls_name = Misc.get_instance_class_name(self)
        result = fmt % (cls_name, len(self.cells))
        return result

    @property
    def cells_count(self):
        total = len(self.cells)
        return total

    @property
    def columns_count(self):
        return self.cells

    @property
    def is_group_of_symbols(self):
        if self._is_symbols_group is None:
            if self.cells:
                fmt = ' *%(p)s( +%(p)s)* *$'
                pat = fmt % dict(p=PATTERN.PUNCTS)
                match = re.match(pat, self.line)
                self._is_symbols_group = bool(match)
            else:
                return False
        return self._is_symbols_group

    def append_new_cell(self, left_pos, right_pos):
        index = len(self.cells)
        ref_cell = self.ref_row.cells[index] if self.ref_row else None
        cell = TabularCell(self.line, left_pos, right_pos, ref_cell=ref_cell)
        if self.ref_row:
            prev_cell = self.cells[-NUMBER.ONE] if index else None
            self.ref_row.aligned and cell.do_first_pass_adjustment(prev_cell=prev_cell)
        self.cells.append(cell)
        return cell

    def process(self):
        self.cells.clear()
        if self.ref_row:
            for ref_cell in self.ref_row.cells:
                left_pos, right_pos = ref_cell.left, ref_cell.right
                cell = self.append_new_cell(left_pos, right_pos)
                bit = 1 if cell.text else 0
                self.row_layout = f'{self.row_layout}{bit}'

    @classmethod
    def do_creating_ref_row(cls, line, pattern, lst, aligned=True):

        if not lst:
            RuntimeException.do_raise_runtime_error(
                obj=Misc.join_string(cls.__name__, 'RTError'),
                msg='Failed to parse\nPattern: %r\nLine: %r' % (pattern, line)
            )

        ref_row = cls(line, aligned=aligned)

        prev_right = 0
        cell = None
        for item in lst:
            left = prev_right
            prev_right = str.index(line, item) if cell is None else prev_right
            right = prev_right + len(item)
            prev_right = right
            cell = ref_row.append_new_cell(left, right)
        else:
            if cell:
                cell.right = 999999

        return ref_row

    @classmethod
    def do_creating_ref_row_by_findall(cls, line, pattern, columns_count=-1):
        lst = re.findall(pattern, line)

        total = len(lst)
        if columns_count > 0 and columns_count != total:
            fmt = ('(Parsed columns: %s) != (expected columns: %s)\n'
                   'Pattern: %r\nLine: %r')
            RuntimeException.do_raise_runtime_error(
                obj=Misc.join_string(cls.__name__, 'RTError'),
                msg=fmt % (total, columns_count, pattern, line)
            )

        ref_row = cls.do_creating_ref_row(line, pattern, lst)
        return ref_row

    @classmethod
    def do_creating_ref_row_by_splitting(cls, line, pattern, columns_count=1):
        separator = pattern
        pattern = re.escape(separator)
        lst = re.split(pattern, line)
        total = len(lst)
        if total == columns_count + NUMBER.TWO:
            prefix, first = lst.pop(NUMBER.ZERO), lst.pop(NUMBER.ZERO)
            new_first = Misc.join_string(prefix, first, sep=separator)
            lst.insert(NUMBER.ZERO, new_first)

            postfix, last = lst.pop(), lst.pop()
            new_last = Misc.join_string(last, postfix, sep=separator)
            lst.append(new_last)
            total = len(lst)

        elif total == columns_count + NUMBER.ONE:
            if line.strip().startswith(separator):
                prefix, first = lst.pop(NUMBER.ZERO), lst.pop(NUMBER.ZERO)
                new_first = Misc.join_string(prefix, first, sep=separator)
                lst.insert(NUMBER.ZERO, new_first)
            elif line.strip().endswith(separator):
                postfix, last = lst.pop(), lst.pop()
                new_last = Misc.join_string(last, postfix, sep=separator)
                lst.append(new_last)

            total = len(lst)

        if columns_count > 0 and columns_count != total:
            fmt = ('(Parsed columns: %s) != (expected columns: %s)\n'
                   'Pattern: %r\nLine: %r')
            RuntimeException.do_raise_runtime_error(
                obj=Misc.join_string(cls.__name__, 'RTError'),
                msg=fmt % (total, columns_count, pattern, line)
            )

        ref_row = cls.do_creating_ref_row(line, pattern, lst, aligned=False)
        return ref_row

    @classmethod
    def do_creating_ref_row_by_variable(cls, line, pattern):
        lst = []
        match = re.match(pattern, line)
        result = match.groupdict()
        for i in range(256):
            key = 'v%03d' % i
            if key in result:
                lst.append(result.get(key))
            else:
                break

        ref_row = cls.do_creating_ref_row(line, pattern, lst)
        return ref_row

    @classmethod
    def create_ref_row(cls, line, pattern, case='', columns_count=-1):
        args = (line, pattern)
        kwargs = dict(columns_count=columns_count)
        if case == 'findall':
            ref_row = cls.do_creating_ref_row_by_findall(*args, **kwargs)
            return ref_row
        elif case == 'variable':
            ref_row = cls.do_creating_ref_row_by_variable(*args)
            return ref_row
        elif case == 'split':
            ref_row = cls.do_creating_ref_row_by_splitting(*args, **kwargs)
            return ref_row
        else:
            RuntimeException.do_raise_runtime_error(
                obj=Misc.join_string(cls.__name__, 'RTError'),
                msg='Unsupported %r case create_ref_row' % case
            )


class TabularColumn:
    def __init__(self, index=0, name='', left_column=None, right_column=None, is_last=False):
        self.left_column = left_column
        self.right_column = right_column
        self.is_last = is_last

        self.extra_data = None

        self.index = index
        self.name = name or 'col%s' % index
        self.cells = []
        self.left_border = NUMBER.ZERO
        self.right_border = NUMBER.ZERO

        self._alignment = 'left'

    def __len__(self):
        chk = bool(self.cells)
        return chk

    def __repr__(self):
        fmt = '%s(name=%r, cells_count=%s)'
        cls_name = Misc.get_instance_class_name(self)
        result = fmt % (cls_name, self.name, len(self.cells))
        return result

    @property
    def cells_count(self):
        total = len(self.cells)
        return total

    @property
    def rows_count(self):
        return self.cells_count

    @property
    def is_left_alignment(self):
        if not self:
            return False
        else:
            chk = self._alignment == 'left'
            return chk

    @property
    def is_right_alignment(self):
        if not self:
            return False
        else:
            chk = self._alignment == 'right'
            return chk

    @property
    def is_center_alignment(self):
        chk = not self.is_left_alignment or not self.is_right_alignment
        return chk

    @property
    def width(self):
        widths = [cell.width for cell in self.cells if cell.width]
        max_width = max(widths)
        are_all_widths_a_same = len(set(widths)) == NUMBER.ONE
        if are_all_widths_a_same:
            return max_width
        else:
            lst_of_left_pos = [cell.left for cell in self.cells]
            are_all_left_pos_a_same = len(set(lst_of_left_pos)) == NUMBER.ONE
            lst_of_right_pos = [cell.right for cell in self.cells]
            are_all_right_pos_a_same = len(set(lst_of_right_pos)) == NUMBER.ONE
            if are_all_left_pos_a_same:
                common_widths, _ = Counter(widths).most_common().pop(0)
                if common_widths == max_width:
                    return max_width
                else:
                    width = math.ceil(statistics.mean(widths))
                    return width
            elif are_all_right_pos_a_same:
                return max_width
            else:
                width = math.ceil(statistics.mean(widths))
                return width

    @property
    def max_edge_trailing_width(self):
        if self.right_column:
            lst = []
            for cell in self.right_column.cells:
                if cell.data.strip():
                    outer_trailing = Misc.get_leading_line(cell.data)
                    lst.append(len(outer_trailing))
            edge_width = max(lst)
            edge_width = NUMBER.ZERO if self.right_column.width == edge_width else edge_width
            return edge_width
        else:
            return NUMBER.ZERO

    @property
    def max_edge_leading_width(self):
        if self.left_column:
            lst = []
            for cell in self.left_column.cells:
                if cell.data.strip():
                    outer_leading = Misc.get_trailing_line(cell.data)
                    lst.append(len(outer_leading))
            edge_width = max(lst)
            edge_width = NUMBER.ZERO if self.left_column.width == edge_width else edge_width
            return edge_width
        else:
            return NUMBER.ZERO

    @property
    def max_width(self):
        width = self.width + self.max_edge_trailing_width + self.max_edge_leading_width
        return width

    @property
    def has_empty_cell(self):
        chk = any(cell.is_empty for cell in self.cells)
        return chk

    def add_extra_data(self, extra_data):
        self.extra_data = extra_data

    def append_cell(self, cell):
        self.cells.append(cell)

    def analyze_and_update_alignment(self):
        if not self.cells:
            return

        lst_of_left_edges = [cell.left + len(cell.leading) for cell in self.cells]
        lst_of_right_edges = [cell.right + len(cell.trailing) for cell in self.cells]
        are_all_left_edges_a_same = len(set(lst_of_left_edges)) == NUMBER.ONE
        are_all_right_edges_a_same = len(set(lst_of_right_edges)) == NUMBER.ONE

        tbl = {'11': 'left', '10': 'left', '01': 'right', '00': 'center'}
        key = f'{int(are_all_left_edges_a_same)}{int(are_all_right_edges_a_same)}'
        self._alignment = tbl.get(key)

    def to_regex(self):
        if not self:
            return STRING.EMPTY

        lst_of_txt = [cell.text for cell in self.cells if cell.text]
        self.extra_data and lst_of_txt.extend(self.extra_data)
        node = TranslatedPattern.do_factory_create(*lst_of_txt)
        pattern = node.get_regex_pattern(var=self.name)
        if node.is_group() and not self.is_last:
            max_items_count = max(cell.items_count for cell in self.cells)
            occurrence = max_items_count - NUMBER.ONE
            if occurrence > NUMBER.ZERO:
                pattern = '%s{,%s})' % (pattern[:-NUMBER.TWO], occurrence)

        if self.has_empty_cell:
            first, last = str.split(pattern, '>', maxsplit=1)
            fmt = '%s>( {%s,%s})|( *%s *))'
            pattern = fmt % (first, self.width, self.max_width, last[:-NUMBER.ONE])
        return pattern

    def to_template_snippet(self, added_list_meta_data=False,
                            skipped_empty=False,
                            to_bared_snippet=False):
        if not self:
            return STRING.EMPTY

        lst_of_txt = [cell.text for cell in self.cells if cell.text]
        self.extra_data and lst_of_txt.extend(self.extra_data)
        node = TranslatedPattern.do_factory_create(*lst_of_txt)
        kwargs = dict() if to_bared_snippet else dict(var=self.name)
        tmpl_snippet = node.get_template_snippet(**kwargs)

        if to_bared_snippet:
            return tmpl_snippet

        if skipped_empty and not added_list_meta_data:
            return tmpl_snippet

        if node.is_group() and not self.is_last:
            max_items_count = max(cell.items_count for cell in self.cells)
            occurrence = max_items_count - NUMBER.ONE
            if occurrence > NUMBER.ZERO:
                if '_phrase' in tmpl_snippet or re.match('(mixed_)?words', tmpl_snippet):
                    fmt = '%s, at_most_%s_phrase_occurrences)'
                else:
                    fmt = '%s, at_most_%s_group_occurrences)'
                tmpl_snippet = node.singular_name + '(' + tmpl_snippet.split('(', 1)[-1]
                tmpl_snippet = fmt % (tmpl_snippet[:-INDEX.ONE], occurrence)

        if added_list_meta_data:
            tmpl_snippet = '%s, meta_data_list)' % tmpl_snippet[:-INDEX.ONE]

        return tmpl_snippet
