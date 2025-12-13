import re

from regexapp import TextPattern

from genericlib import Misc, STRING, Wildcard, NUMBER, PATTERN
from genericlib import Text
from textfsmgen.gp import TranslatedPattern


class GPCommon:

    @classmethod
    def get_line_position_by(cls, lines, item):
        if item is None:
            return None

        pat1 = r'(?i)^\s+--regex\s+'
        pat2 = r'(?i)^\s+--wildcard\s+'

        if Misc.is_string(item):
            pattern = TextPattern(item)
            if re.search(pat1, item):
                pattern = re.sub(pat1, STRING.EMPTY, item)
            elif re.search(pat2, item):
                txt = re.sub(pat2, STRING.EMPTY, item)
                pattern = Wildcard(txt).pattern
            for index, line in enumerate(lines):
                if re.search(pattern, line, re.I):
                    return index
        else:
            is_number, index = Misc.try_to_get_number(item, return_type=int)
            total_lines_count = len(lines)
            if is_number:
                return None if index > total_lines_count - NUMBER.ONE else index

        return None

    @classmethod
    def get_fixed_line_snippet(cls, lines, line='', index=None):
        if index is not None:
            line = lines[index]

        if not line.strip():
            ws = 'whitespace' if line.strip(STRING.SPACE_CHAR) else 'space'
            snippet = f'start() end({ws})'
            return snippet

        lst = Text(line.strip()).do_finditer_split(PATTERN.NON_WHITESPACES)
        for i, item in enumerate(lst):
            if item.strip():
                factory = TranslatedPattern.do_factory_create(item)
                if factory.name in ['digit', 'digits', 'number', 'mixed_number']:
                    lst[i] = factory.get_template_snippet()
        snippet = Misc.join_string(*lst)
        leading = Misc.get_leading_line(line)
        trailing = Misc.get_trailing_line(line)
        snippet = f'{leading}{snippet}{trailing}'

        return snippet
