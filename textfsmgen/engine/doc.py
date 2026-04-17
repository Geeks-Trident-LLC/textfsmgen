class TokenDoc:
    """Provide short, human-readable descriptions for token names."""

    def __init__(self, name: str, or_empty: bool = False):
        self.name = name
        self.or_empty = or_empty

    @staticmethod
    def singular_placeholder(key: str) -> str:
        """Return a placeholder description template for singular token types."""
        templates = {
            # Basic character classes
            "dot"               : "match %s ASCII or Unicode character.",
            "space"             : "match %s space character.",
            "ws"                : "match %s whitespace character.",
            "whitespace"        : "match %s whitespace character.",
            "digit"             : "match %s digit character.",
            "letter"            : "match %s letter character.",
            "alnum"             : "match %s alphanumeric character.",
            "punct"             : "match %s punctuation character.",
            "punctuation"       : "match %s punctuation character.",
            "graph"             : "match %s visible character (\\x21–\\x7e).",
            "non_ws"            : "match %s non‑whitespace character.",
            "non_whitespace"    : "match %s non‑whitespace character.",

            # Space or punctuation
            "space_punct"           : "match %s space or punctuation character.",
            "space_or_punct"        : "match %s space or punctuation character.",
            "space_or_punctuation"  : "match %s space or punctuation character.",

            "punct_space"           : "match %s space or punctuation character.",
            "punct_or_space"        : "match %s space or punctuation character.",
            "punctuation_or_space"  : "match %s space or punctuation character.",

            "sop"                   : "match %s space or punctuation character.",
            "sp"                    : "match %s space or punctuation character.",

            # Letter or punctuation
            "letter_punct"          : "match %s letter or punctuation character.",
            "letter_or_punct"       : "match %s letter or punctuation character.",
            "letter_or_punctuation" : "match %s letter or punctuation character.",

            "lop"                   : "match %s letter or punctuation character.",
            "lp"                    : "match %s letter or punctuation character.",
        }

        return templates.get(key, "")

    @staticmethod
    def plural_placeholder(key):
        """Return a placeholder description template for plural token types."""
        templates = {
            "dots"              : "match %s ASCII or Unicode characters.",
            "spaces"            : "match %s space characters.",
            "wss"               : "match %s whitespace characters.",
            "whitespaces"       : "match %s whitespace characters.",
            "digits"            : "match %s digit characters.",
            "letters"           : "match %s letter characters.",

            "puncts"            : "match %s punctuation characters.",
            "punctuations"      : "match %s punctuation characters.",
            "non_wss"           : "match %s non-whitespace characters.",
            "non_whitespaces"   : "match %s non-whitespace characters.",

            # Space or punctuation
            "spaces_puncts"             : "match %s space or punctuation character.",
            "spaces_or_puncts"          : "match %s space or punctuation character.",
            "spaces_or_punctuations"    : "match %s space or punctuation character.",

            "puncts_spaces"             : "match %s space or punctuation character.",
            "puncts_or_spaces"          : "match %s space or punctuation character.",
            "punctuations_or_spaces"    : "match %s space or punctuation character.",

            "sops"                      : "match %s space or punctuation character.",
            "sps"                       : "match %s space or punctuation character.",

            # Letter or punctuation
            "letters_puncts"            : "match %s letter or punctuation character.",
            "letters_or_puncts"         : "match %s letter or punctuation character.",
            "letters_or_punctuations"   : "match %s letter or punctuation character.",

            "puncts_letters"            : "match %s letter or punctuation character.",
            "puncts_or_letters"         : "match %s letter or punctuation character.",
            "punctuations_or_letters"   : "match %s letter or punctuation character.",

            "lops"                      : "match %s letter or punctuation character.",
            "lps"                       : "match %s letter or punctuation character.",
        }
        return templates.get(key, "")

    @staticmethod
    def semantic_placeholder(key: str) -> str:
        """Return a placeholder description template for semantic token types."""
        templates = {
            # Word‑like tokens
            "word": (
                "match %s word containing alphanumeric or underscore characters "
                "with at least one alphabetic character."
            ),
            "mixed_word": (
                "match %s mixed word containing alphanumeric or punctuation "
                "characters with at least one alphanumeric character."
            ),

            # Number‑like tokens
            "number": "match %s sequence of numeric characters or a floating‑point number.",
            "mixed_number": (
                "match %s sequence of numeric characters or a floating‑point number "
                "optionally surrounded by "
                "number‑related punctuation such as +, -, %%, (, ), or $."
            ),
        }

        return templates.get(key, "")

    @staticmethod
    def plural_semantic_placeholder(key: str) -> str:
        """Return a placeholder description template for multi‑word semantic tokens."""
        templates = {
            "words": (
                "match %s words containing alphanumeric or underscore characters, "
                "each with at least one alphabetic character, separated by one or "
                "more whitespace characters."
            ),
            "mixed_words": (
                "match %s mixed words containing alphanumeric or punctuation "
                "characters, each with at least one alphanumeric character, "
                "separated by one or more whitespace characters."
            ),
        }

        return templates.get(key, "")

    @staticmethod
    def grouped_placeholder(key):

        templates = {
            "letters_group": (
                "match %s sequences of alphabetic characters, each separated "
                "by one or more whitespace characters."
            ),
            "digits_group": (
                "match %s sequences of numeric characters, each separated "
                "by one or more whitespace characters."
            ),
            "number_group": (
                "match %s numbers, each separated by one or more "
                "whitespace characters."
            ),
            "mixed_number_group": (
                "match %s mixed numbers, each separated by one or more "
                "whitespace characters."
            ),
            "puncts_group": (
                "match %s sequences of punctuation characters, each separated "
                "by one or more whitespace characters."
            ),
            "punctuations_group": (
                "match %s sequences of punctuation characters, each separated "
                "by one or more whitespace characters."
            ),
            "non_wss_group": (
                "match %s sequences of non‑whitespace characters, each "
                "separated by one or more whitespace characters."
            ),
            "non_whitespaces_group": (
                "match %s sequences of non‑whitespace characters, each "
                "separated by one or more whitespace characters."
            ),
        }
        return templates.get(key, "")

    def describe_core(self) -> str:
        """Return a brief description for the core keyword based on its token type."""
        or_empty = self.or_empty is True

        groups = [
            ("zero or one"  if or_empty else "one",         self.singular_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_placeholder),
            ("zero or one"  if or_empty else "one",         self.semantic_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_semantic_placeholder),
            ("zero or more" if or_empty else "two or more", self.grouped_placeholder),
        ]

        key = self.name
        for replacement, func in groups:
            template = func(key)
            if template:
                return template % replacement
        return ""

    def describe_optional(self) -> str:

        if not self.name.startswith("optional_"):
            return ""

        or_empty = self.or_empty is True

        groups = [
            ("zero or one",     self.singular_placeholder),
            ("zero or more",    self.plural_placeholder),
            ("zero or one",     self.semantic_placeholder),
            ("zero or more",    self.plural_semantic_placeholder),
            ("zero or more" if or_empty else "one or more", self.grouped_placeholder),
        ]

        key = self.name.removeprefix("optional_")

        for replacement, func in groups:
            template = func(key)
            if template:
                return template % replacement
        return ""


    def describe_some(self) -> str:
        or_empty = self.or_empty is True

        groups = [
            ("zero or more" if or_empty else "one or more", self.singular_placeholder),
            # ("zero or more" if or_empty else "one or more", self.plural_placeholder),
            # ("zero or one"  if or_empty else "one or more", self.semantic_placeholder),
            # ("zero or more" if or_empty else "one or more", self.plural_semantic_placeholder),
            ("zero or more" if or_empty else "two or more", self.grouped_placeholder),
        ]
        key = self.name.removeprefix("some_")
        for replacement, func in groups:
            template = func(key)
            if template:
                return template % replacement
        return ""