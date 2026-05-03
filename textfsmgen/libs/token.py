"""
textfsmgen.libs.common
======================

Token classes and tokenizer for parsing keyword calls and text segments.
"""


import re


class BaseText(str):
    """
    Lightweight string wrapper that normalizes input into a UTF‑8 string.
    """
    def __new__(cls, value):
        if isinstance(value, bytes):
            data = value.decode("utf-8")
        elif isinstance(value, str):
            data = value
        elif value is None:
            data = ""
        else:
            data = str(value)
        return super().__new__(cls, data)

    @property
    def is_empty(self): return self == ""

    @property
    def is_whitespace(self): return bool(re.fullmatch(r"\s+", self))

    @property
    def has_data(self): return bool(self.strip())

    @property
    def is_plain(self): return isinstance(self, TextNode)


class TextNode(BaseText):
    """
    Represents a plain text token (non‑call).
    """
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"TextNode({self.value!r})"


class CallNode(BaseText):
    """
    Represents a keyword-style call: name(param1, param2, ...).
    Parameters remain raw strings (not recursively parsed).
    """
    _name_pattern = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, raw: str):
        self._raw = raw
        self._name = ""
        self._params = []
        self._parsed = False
        self._parse()

    def __bool__(self): return self._parsed

    def __len__(self): return 1 if self else 0

    def __repr__(self):
        return f"CallNode(name={self._name!r}, params={self._params!r})"

    @property
    def name(self): return self._name

    @property
    def params(self): return self._params

    @property
    def has_no_parameters(self): return not self._params

    @property
    def raw(self): return self._raw

    @property
    def value(self): return self._raw

    @property
    def new(self):
        if not self:
            return self.__class__("unknown()")
        params_text = ", ".join(self._params)
        return self.__class__(f"{self._name}({params_text})")

    # -----------------------------
    # Internal parsing
    # -----------------------------
    def _parse(self):
        """
        Parse raw text into name + parameter list.
        """
        if "(" not in self._raw or not self._raw.endswith(")"):
            return

        name, param_text = self._raw[:-1].split("(", maxsplit=1)

        # Reject invalid or placeholder names
        if not name or name.lower() in {"undefined", "unknown"}:
            return

        # Reject names that fail the pattern
        if not self._name_pattern.fullmatch(name):
            return

        self._name = name.lower()
        self._params = self._split_params(param_text)
        self._parsed = True

    def _split_params(self, text: str) -> list[str]:    # noqa
        """
        Split parameters by commas at top level (ignore commas inside nested calls).
        """

        if not text.strip():
            return []

        params = []
        depth = 0
        start = 0

        for i, ch in enumerate(text):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                params.append(text[start:i].strip())
                start = i + 1

        last = text[start:].strip()
        if last:
            params.append(last)

        return params

    def add_parameter(self, param: str):
        """Append a parameter to the end of the list."""
        self._params.append(param)

    def prepend_parameter(self, param: str):
        """Insert a parameter at the beginning of the list."""
        self._params.insert(0, param)

    def insert_parameter_at(self, index: int, param: str):
        """Insert a parameter at the specified index."""
        self._params.insert(index, param)

    def remove_parameter(self, param: str):
        """Remove the first matching parameter if present."""
        if param in self._params:
            self._params.remove(param)
            return param
        return ""

    def remove_matching_parameter(self, pattern: str):
        """Remove and return the first parameter matching the regex pattern, or ''."""
        for param in self._params:
            if re.fullmatch(pattern, param):
                self._params.remove(param)
                return param
        return ""

    def has_parameter(self, value: str) -> bool:
        """Return True if a parameter exactly matches the given value."""
        return value in self._params

    def has_matching_parameter(self, pattern: str) -> bool:
        """Return True if any parameter matches the given regex pattern."""
        return any(re.fullmatch(pattern, p) for p in self._params)

    def with_parameters(self, *params: str):
        """Return a new instance with the given parameters."""
        params_text = ", ".join(params)
        return self.__class__(f"{self._name}({params_text})")


def tokenize(text: str):
    """Tokenize into TextNode and CallNode objects, preserving whitespace."""
    tokens = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # ----------------------------------------
        # Whitespace → store as TextNode
        # ----------------------------------------
        if ch.isspace():
            start = i
            while i < n and text[i].isspace():
                i += 1
            tokens.append(TextNode(text[start:i]))
            continue

        # ----------------------------------------
        # Keyword call: <name>(...)
        # ----------------------------------------
        if ch.isalnum() or ch == "_":
            start = i

            # read keyword name
            while i < n and (text[i].isalnum() or text[i] == "_"):
                i += 1

            # if next char is '(', parse call
            if i < n and text[i] == "(":
                depth = 0
                j = i
                while j < n:
                    if text[j] == "(":
                        depth += 1
                    elif text[j] == ")":
                        depth -= 1
                        if depth == 0:
                            tokens.append(CallNode(text[start:j + 1]))
                            i = j + 1
                            break
                    j += 1
                else:
                    # malformed → treat as text
                    tokens.append(TextNode(text[start:]))
                    return tokens
                continue

            # plain text word
            tokens.append(TextNode(text[start:i]))
            continue

        # ----------------------------------------
        # Text token (punctuation, symbols, numbers)
        # ----------------------------------------
        start = i
        while i < n and not text[i].isspace():
            # stop before keyword call start
            if text[i].isalnum() or text[i] == "_":
                look = i
                while look < n and (text[look].isalnum() or text[look] == "_"):
                    look += 1
                if look < n and text[look] == "(":
                    break
            i += 1

        tokens.append(TextNode(text[start:i]))

    return tokens
