
from textfsmgen.tools.token import WhitespaceSnippet

class SnippetTranslator:
    def __init__(
        self, raw, variable_flag=True, notation_flag=False,
        group_flag=False, exact_flag=False, split_arg="/"
    ):
        self.raw = raw

        self.variable_flag = variable_flag
        self.notation_flag = notation_flag
        self.group_flag = group_flag
        self.exact_flag = exact_flag
        self.split_arg = split_arg

        self._parsed = False
        self._snippet = ""
        self.parse()


    def __bool__(self): return self._parsed

    def __len__(self): return 1 if self._parsed else 0

    @property
    def snippet(self): return self._snippet

    def parse(self):
        node = WhitespaceSnippet(self.raw, var_name="v1")
        self._parsed = bool(node)
        self._snippet = node.snippet


class IterateTranslator:
    def __init__(self, original):
        self.original = original
