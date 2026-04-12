
from textfsmgen.tools.token import WhitespaceSnippet

class SnippetTranslator:
    def __init__(
        self, raw, variable_flag=True, notation_flag=False,
        group_flag=False, generic_flag=False, split_arg="/"
    ):
        self._raw = raw

        self.variable_flag = variable_flag
        self.notation_flag = notation_flag
        self.group_flag = group_flag
        self.generic_flag = generic_flag
        self.split_arg = split_arg

        self._parsed = False
        self._snippet = ""
        self.parse()


    def __bool__(self): return self._parsed

    def __len__(self): return 1 if self._parsed else 0

    @property
    def raw(self): return self._raw

    @property
    def parsed(self): return self._parsed

    @property
    def snippet(self): return self._snippet

    def parse(self):
        """Run available parsers and stop at the first successful match."""
        parsers = [self._parse_whitespace]

        for parser in parsers:
            if parser():
                return

    def _parse_whitespace(self):
        """Parse raw text as a whitespace snippet."""
        node = WhitespaceSnippet(self._raw, var_name="v0")
        self._parsed = bool(node)
        self._snippet = node.snippet
        return self._parsed


class IterateTranslator:
    def __init__(self, original):
        self.original = original
