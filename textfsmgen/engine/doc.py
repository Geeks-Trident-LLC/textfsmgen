"""
textfsmgen.engine.doc
=====================

Token Documentation utilities for the TextFSM Generator framework.
"""

import re

from textfsmgen.libs import number
from textfsmgen.libs.pattern import PATTERN

from textfsmgen.exceptions import raise_runtime_error


def get_singular_placeholders():
    """Return a list of singular placeholder description templates."""
    placeholders = {
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
        "space_or_punct"        : "match %s space or punctuation character.",
        "punct_or_space"        : "match %s space or punctuation character.",
        "sop"                   : "match %s space or punctuation character.",
        "pos"                   : "match %s space or punctuation character.",

        # Letter or punctuation
        "letter_or_punct"       : "match %s letter or punctuation character.",
        "punct_or_letter"       : "match %s letter or punctuation character.",
        "lop"                   : "match %s letter or punctuation character.",
        "pol"                   : "match %s letter or punctuation character.",
    }

    for singular in PATTERN.singular_keywords:
        if singular not in placeholders:
            raise_runtime_error(
                obj="UndefinedKeywordDescription",
                msg=(
                    f"Missing document description for {singular!r} keyword. "
                    "Report this to the Development Team."
                )
            )

    return placeholders

def get_plural_placeholders():
    """Return a list of plural placeholder description templates."""
    placeholders = {}

    for singular, singular_desc in get_singular_placeholders().items():
        plural = PATTERN.resolve_plural(singular)
        plural_desc = singular_desc.replace("character", "characters")
        placeholders[plural] = plural_desc
    return placeholders


def get_semantic_placeholders():
    """Return a list of semantic placeholder description templates."""
    placeholders = {
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

    for semantic in PATTERN.semantic_keywords:
        if semantic not in placeholders:
            raise_runtime_error(
                obj="UndefinedKeywordDescription",
                msg=(
                    f"Missing document description for {semantic!r} keyword. "
                    "Report this to the Development Team."
                )
            )

    return placeholders


def get_plural_semantic_placeholders():
    """Return a list of plural-semantic placeholder description templates."""
    placeholders = {}

    for semantic, semantic_desc in get_semantic_placeholders().items():
        plural_semantic = PATTERN.resolve_plural_semantic(semantic)
        plural_semantic_desc = semantic_desc.replace(" word ", " words ")
        plural_semantic_desc = plural_semantic_desc.replace(
            ".",
            ", separated by one or more whitespace characters."
        )

        placeholders[plural_semantic] = plural_semantic_desc
    return placeholders

def get_grouped_placeholders():
    """Return a list of grouped placeholder description templates."""
    # --------------------------------------------------------------------------
    def expand_format_placeholders(text):
        """Expand %s and trailing dots into descriptive placeholder text."""
        updated = text.replace("%s", "%s sequences of")
        updated = updated.replace(
            ".",
            ", each separated by one or more whitespace characters."
        )
        return updated
    # --------------------------------------------------------------------------

    placeholders = {}

    singular_placeholders = get_singular_placeholders()
    plural_placeholders = get_plural_placeholders()
    semantic_placeholders = get_semantic_placeholders()
    plural_semantic_placeholders = get_plural_semantic_placeholders()

    special = ["dots", "spaces", "wss", "whitespaces"]

    for singular in singular_placeholders:
        keyword = f"{singular}_group"
        plural = PATTERN.resolve_plural(singular)
        plural_desc = plural_placeholders.get(plural, "")
        if plural in special:
            placeholders[keyword] = plural_desc
            continue
        placeholders[keyword] = expand_format_placeholders(plural_desc)

    for plural, desc in plural_placeholders.items():
        keyword = f"{plural}_group"
        if plural in special:
            placeholders[keyword] = desc
            continue
        placeholders[keyword] = expand_format_placeholders(desc)

    for semantic in semantic_placeholders:
        keyword = f"{semantic}_group"
        plural_semantic = PATTERN.resolve_plural_semantic(semantic)
        placeholders[keyword] = plural_semantic_placeholders[plural_semantic]

    for plural_semantic, desc in plural_semantic_placeholders.items():
        keyword = f"{plural_semantic}_group"
        placeholders[keyword] = desc

    return placeholders


def get_items_placeholders():
    """Return a list of grouped placeholder description templates."""
    # --------------------------------------------------------------------------
    def expand_format_placeholders(text):
        """Expand %s and trailing dots into descriptive placeholder text."""
        updated = text.replace("%s", "%s sequences of")
        updated = updated.replace(
            ".",
            ", each separated by one or more whitespace characters."
        )
        return updated
    # --------------------------------------------------------------------------

    placeholders = {}

    singular_placeholders = get_singular_placeholders()
    plural_placeholders = get_plural_placeholders()
    semantic_placeholders = get_semantic_placeholders()
    plural_semantic_placeholders = get_plural_semantic_placeholders()

    special = ["dots", "spaces", "wss", "whitespaces"]

    for singular in singular_placeholders:
        keyword = f"{singular}_items"
        plural = PATTERN.resolve_plural(singular)
        plural_desc = plural_placeholders.get(plural, "")
        if plural in special:
            placeholders[keyword] = plural_desc
            continue
        placeholders[keyword] = expand_format_placeholders(plural_desc)

    for plural, desc in plural_placeholders.items():
        keyword = f"{plural}_items"
        if plural in special:
            placeholders[keyword] = desc
            continue
        placeholders[keyword] = expand_format_placeholders(desc)

    for semantic in semantic_placeholders:
        keyword = f"{semantic}_items"
        plural_semantic = PATTERN.resolve_plural_semantic(semantic)
        placeholders[keyword] = plural_semantic_placeholders[plural_semantic]

    for plural_semantic, desc in plural_semantic_placeholders.items():
        keyword = f"{plural_semantic}_items"
        placeholders[keyword] = desc

    return placeholders


class TokenDoc:
    """Provide short, human-readable descriptions for token names."""

    def __init__(self, name: str, or_empty: bool = False):
        self.name = name
        self.or_empty = or_empty

        self._singular_placeholders = get_singular_placeholders()
        self._plural_placeholders = get_plural_placeholders()
        self._semantic_placeholders = get_semantic_placeholders()
        self._plural_semantic_placeholders = get_plural_semantic_placeholders()
        self._grouped_placeholders = get_grouped_placeholders()
        self._items_placeholders = get_items_placeholders()
        self._usage = ""
        self.process()

    @property
    def usage(self): return self._usage

    def singular_placeholder(self, keyword: str) -> str:
        """Return a placeholder description template for singular token types."""
        return self._singular_placeholders.get(keyword, "")

    def plural_placeholder(self, keyword):
        """Return a placeholder description template for plural token types."""
        return self._plural_placeholders.get(keyword, "")

    def semantic_placeholder(self, keyword: str) -> str:
        """Return a placeholder description template for semantic token types."""
        return self._semantic_placeholders.get(keyword, "")

    def plural_semantic_placeholder(self, keyword: str) -> str:
        """Return a placeholder description template for multi‑word semantic tokens."""
        return self._plural_semantic_placeholders.get(keyword, "")

    def grouped_placeholder(self, keyword):
        """Return a placeholder description template for grouped token types."""
        return self._grouped_placeholders.get(keyword, "")

    def describe_custom(self):
        if self.name in ("anything", "something"):
            template = self._plural_placeholders.get("dots")
            if self.name == "something" and not self.or_empty:
                return template % "one or more"
            return template % "zero or more"
        return ""

    def describe_core(self) -> str:
        """Return a brief description for the core keyword based on its token type."""
        or_empty = self.or_empty is True

        groups = [
            ("zero or one"  if or_empty else "one",         self.singular_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_placeholder),
            ("zero or one"  if or_empty else "one",         self.semantic_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_semantic_placeholder),
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

        groups = [
            ("zero or one",     self.singular_placeholder),
            ("zero or more",    self.plural_placeholder),
            ("zero or one",     self.semantic_placeholder),
            ("zero or more",    self.plural_semantic_placeholder),
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
            ("zero or more" if or_empty else "one or more", self.plural_placeholder),
            ("zero or more"  if or_empty else "one or more", self.semantic_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_semantic_placeholder),
        ]

        key = self.name.removeprefix("some_")

        actual_keyword = key

        if PATTERN.keyword_in(key, singular=True, plural=True):
            actual_keyword = PATTERN.resolve_plural(key)
        elif PATTERN.keyword_in(key, semantic=True, plural_semantic=True):
            actual_keyword = PATTERN.resolve_plural_semantic(key)

        for replacement, func in groups:
            template = func(actual_keyword)
            if template:
                return template % replacement
        return ""

    def describe_zero_or_one(self) -> str:

        if not self.name.startswith("zero_or_one_"):
            return ""

        # or_empty = self.or_empty is True

        groups = [
            ("zero or one",     self.singular_placeholder),
            ("zero or more",    self.plural_placeholder),
            ("zero or one",     self.semantic_placeholder),
            ("zero or more",    self.plural_semantic_placeholder),
        ]

        key = self.name.removeprefix("zero_or_one_")

        for replacement, func in groups:
            template = func(key)
            if template:
                return template % replacement
        return ""

    def describe_zero_or_more(self) -> str:

        if not self.name.startswith("zero_or_more_"):
            return ""

        # or_empty = self.or_empty is True

        groups = [
            ("zero or more",    self.singular_placeholder),
            ("zero or more",    self.plural_placeholder),
            ("zero or more",    self.semantic_placeholder),
            ("zero or more",    self.plural_semantic_placeholder),
        ]

        key = self.name.removeprefix("zero_or_more_")

        actual_keyword = key

        if PATTERN.keyword_in(key, singular=True, plural=True):
            actual_keyword = PATTERN.resolve_plural(key)
        elif PATTERN.keyword_in(key, semantic=True, plural_semantic=True):
            actual_keyword = PATTERN.resolve_plural_semantic(key)

        for replacement, func in groups:
            template = func(actual_keyword)
            if template:
                return template % replacement
        return ""

    def describe_one_or_more(self) -> str:

        if not self.name.startswith("one_or_more_"):
            return ""

        or_empty = self.or_empty is True

        groups = [
            ("zero or more" if or_empty else "one or more", self.singular_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_placeholder),
            ("zero or more" if or_empty else "one or more", self.semantic_placeholder),
            ("zero or more" if or_empty else "one or more", self.plural_semantic_placeholder),
        ]

        key = self.name.removeprefix("one_or_more_")

        actual_keyword = key

        if PATTERN.keyword_in(key, singular=True, plural=True):
            actual_keyword = PATTERN.resolve_plural(key)
        elif PATTERN.keyword_in(key, semantic=True, plural_semantic=True):
            actual_keyword = PATTERN.resolve_plural_semantic(key)

        for replacement, func in groups:
            template = func(actual_keyword)
            if template:
                return template % replacement
        return ""

    def describe_group(self) -> str:

        special = [
            "dot_group", "dots_group", "space_group", "spaces_group",
            "ws_group", "wss_group", "whitespace_group", "whitespaces_group"]

        if not self.name.endswith("_group"):
            return ""

        is_optional = self.name.startswith("optional_")
        keyword = self.name.removeprefix("optional_")
        template = self._grouped_placeholders.get(keyword, "")

        if not template:
            return ""

        if self.or_empty or is_optional:
            return template % "zero or more"

        replacement = "one or more" if keyword in special else "two or more"
        return template % replacement

    def describe_items(self) -> str:

        if not self.name.endswith("_items"):
            return ""

        is_optional = self.name.startswith("optional_")
        keyword = self.name.removeprefix("optional_")
        template = self._items_placeholders.get(keyword, "")

        if not template:
            return ""

        if self.or_empty or is_optional:
            return template % "zero or more"

        return template % "one or more"

    def get_exact_quantity_and_keyword(self):
        """Return (quantity, keyword) for patterns like '3_word' or 'three_word'."""
        name = self.name

        # --- Numeric quantity -----------------------------------------------------
        m = re.fullmatch(r"(?P<qty>\d+)_?(?P<keyword>\w+)", name)
        if m:
            return m.group("qty"), m.group("keyword")

        # --- Word quantity --------------------------------------------------------
        m = re.fullmatch(r"(?P<qty>[A-Za-z]+(?:-[A-Za-z]+)?)_(?P<keyword>\w+)",
                         name)
        if m:
            word_qty = m.group("qty")
            value = number.word_to_digit(word_qty)
            if isinstance(value, int):
                return str(value), m.group("keyword")

        return "", ""

    def describe_exact_match(self) -> str:
        """Return a human‑readable description for exact quantity patterns like '3_word'."""
        qty, keyword = self.get_exact_quantity_and_keyword()
        if not qty.isdigit():
            return ""
        qty = int(qty)
        word_qty = number.digit_to_word(qty)

        # Helper: choose singular vs plural placeholder based on qty
        def resolve_placeholder(singular_key, plural_key):
            if qty <= 1:
                return self._singular_placeholders.get(singular_key, "")
            return self._plural_placeholders.get(plural_key, "")

        # 1. Singular keyword family
        if keyword in self._singular_placeholders:
            plural = PATTERN.resolve_plural(keyword)
            template = resolve_placeholder(keyword, plural)
            return template % f"exactly {word_qty}"

        # 2. Plural keyword family
        if keyword in self._plural_placeholders:
            singular = PATTERN.resolve_singular(keyword)
            template = resolve_placeholder(singular, keyword)
            return template % f"exactly {word_qty}"

        # 3. Semantic keyword family
        if keyword in self._semantic_placeholders:
            if qty <= 1:
                template = self._semantic_placeholders.get(keyword, "")
            else:
                plural_sem = PATTERN.resolve_plural_semantic(keyword)
                template = self._plural_semantic_placeholders.get(plural_sem,
                                                                  "")
            return template % f"exactly {word_qty}"

        # 4. Plural semantic keyword family
        if keyword in self._plural_semantic_placeholders:
            if qty <= 1:
                plural_sem = PATTERN.resolve_plural_semantic(keyword)
                template = self._plural_semantic_placeholders.get(plural_sem,
                                                                  "")
            else:
                template = self._plural_semantic_placeholders.get(keyword, "")
            return template % f"exactly {word_qty}"

        return ""

    def process(self):
        methods = [
            self.describe_custom,
            self.describe_core,
            self.describe_optional,
            self.describe_some,
            self.describe_zero_or_one,
            self.describe_zero_or_more,
            self.describe_one_or_more,
            self.describe_group,
            self.describe_items,
            self.describe_exact_match,
        ]

        for method in methods:
            result = method()
            if result:
                self._usage = result
                return