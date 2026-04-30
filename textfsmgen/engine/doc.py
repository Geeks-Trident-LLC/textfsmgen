"""
textfsmgen.engine.doc
=====================

Token Documentation utilities for the TextFSM Generator framework.
"""

import re
from textwrap import indent

from textfsmgen.core.patterns import ElementPattern
from textfsmgen.libs.text import wrap_text_block, enclose_string
from textfsmgen.libs.number import word_to_digit
from textfsmgen.libs import number
from textfsmgen.libs.pattern import PATTERN
from textfsmgen.libs.pattern import ParsedKeywordMappingName

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


class OperationDoc:
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
        self._doc = ""
        self.process()

    @property
    def doc(self): return self._doc

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
            if str(value).isdigit():
                return value, m.group("keyword")

        return "", ""

    def describe_exact_match(self) -> str:
        """Return a human‑readable description for exact quantity patterns like '3_word'."""
        qty, keyword = self.get_exact_quantity_and_keyword()
        if not qty.isdigit():
            return ""
        qty = int(qty)
        word_qty = number.digit_to_word(qty)
        replacement = f"either zero or exactly {word_qty}" if self.or_empty else f"exactly {word_qty}"

        # Helper: choose singular vs plural placeholder based on qty
        def resolve_placeholder(singular_key, plural_key):
            if qty <= 1:
                return self._singular_placeholders.get(singular_key, "")
            return self._plural_placeholders.get(plural_key, "")

        # 1. Singular keyword family
        if keyword in self._singular_placeholders:
            plural = PATTERN.resolve_plural(keyword)
            template = resolve_placeholder(keyword, plural)
            return template % replacement

        # 2. Plural keyword family
        if keyword in self._plural_placeholders:
            singular = PATTERN.resolve_singular(keyword)
            template = resolve_placeholder(singular, keyword)
            return template % replacement

        # 3. Semantic keyword family
        if keyword in self._semantic_placeholders:
            if qty <= 1:
                template = self._semantic_placeholders.get(keyword, "")
            else:
                plural_sem = PATTERN.resolve_plural_semantic(keyword)
                template = self._plural_semantic_placeholders.get(plural_sem,"")
            return template % replacement

        # 4. Plural semantic keyword family
        if keyword in self._plural_semantic_placeholders:
            if qty <= 1:
                plural_sem = PATTERN.resolve_plural_semantic(keyword)
                template = self._plural_semantic_placeholders.get(plural_sem,"")
            else:
                template = self._plural_semantic_placeholders.get(keyword, "")
            return template % replacement

        return ""

    def get_range_quantity_and_keyword(self):
        """
        Extract a ranged quantity and keyword from names like '1_to_3_word'.
        Returns (lo, hi, keyword) as integers and a string.
        """
        pat = r"(?i)(?P<lo>[a-z0-9]*)_(to_)?(?P<hi>[a-z0-9]*)_(?P<keyword>\w+)"
        m = re.match(pat, self.name)
        if not m:
            return None, None, None

        raw_lo = m.group("lo") or "0"
        raw_hi = m.group("hi")
        raw_hi = "99999" if raw_hi in ("", "n") else raw_hi

        lo = word_to_digit(raw_lo, as_str=False)
        hi = word_to_digit(raw_hi, as_str=False)
        keyword = m.group("keyword")

        return lo, hi, keyword

    def describe_range_match(self):
        """Return a human-readable description for ranged quantity keywords."""
        lo, hi, keyword = self.get_range_quantity_and_keyword()
        if hi is None and lo is None:
            return ""

        # Invalid: start > end
        if lo > hi:
            return (
                f"{self.name} is invalid: range({lo}, {hi + 1}) cannot count "
                f"forward because start ({lo}) >= end ({hi}+1).")

        size = hi - lo

        word_digit_lo = number.digit_to_word(lo)
        word_digit_hi = number.digit_to_word(hi)

        # --- EXACT MATCH CASE ----------------------------------------------------
        if size == 0:
            template = ""
            if keyword in self._singular_placeholders or keyword in self._plural_placeholders:
                singular = PATTERN.resolve_singular(keyword)
                template = self._singular_placeholders.get(singular, "")
            elif keyword in self._semantic_placeholders or keyword in self._plural_semantic_placeholders:
                semantic = PATTERN.resolve_semantic(keyword)
                template = self._semantic_placeholders.get(semantic, "")

            if PATTERN.keyword_in(keyword, singular=True, plural=True):
                if lo == 1:
                    singular = PATTERN.resolve_singular(keyword)
                    template = self._singular_placeholders.get(singular, "")
                elif lo > 1:
                    plural = PATTERN.resolve_plural(keyword)
                    template = self._plural_semantic_placeholders.get(plural, "")
            elif keyword in self._semantic_placeholders or keyword in self._plural_semantic_placeholders:
                if lo == 1:
                    semantic = PATTERN.resolve_semantic(keyword)
                    template = self._semantic_placeholders.get(semantic, "")
                elif lo > 1:
                    plural_semantic = PATTERN.resolve_plural_semantic(keyword)
                    template = self._plural_semantic_placeholders.get(plural_semantic, "")

            if template:
                replacement = (
                    f"either zero or exactly {word_digit_lo}"
                    if self.or_empty else
                    f"exactly {word_digit_lo}"
                )
                return template % replacement
            return f"{self.name} is invalid snippet keyword."

        # --- RANGE MATCH CASE ----------------------------------------------------
        template = ""
        if keyword in self._singular_placeholders or keyword in self._plural_placeholders:
            plural = PATTERN.resolve_plural(keyword)
            template = self._singular_placeholders.get(plural, "")
        elif keyword in self._semantic_placeholders or keyword in self._plural_semantic_placeholders:
            plural_semantic = PATTERN.resolve_plural_semantic(keyword)
            template = self._plural_semantic_placeholders.get(plural_semantic, "")

        if template:
            if self.or_empty:
                replacement = (
                    f"zero or more"
                    if hi == 99999 else
                    f"either zero or {word_digit_lo} to {word_digit_hi}"
                )
            else:
                replacement = (
                    f"{word_digit_lo} or more"
                    if hi == 99999 else
                    f"{word_digit_lo} to {word_digit_hi}"
                )
            return template % replacement
        return f"{self.name} is invalid snippet keyword."

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
            self.describe_range_match
        ]

        for method in methods:
            result = method()
            if result:
                self._doc = result
                return


class ExplanationDoc:
    def __init__(self, snippet):
        self._snippet = snippet

        self._pattern = ""
        self._keyword = ""
        self._base_keyword = ""
        self._var_name = ""
        self._allowed_empty = False
        self._quantity = ""
        self._quantity_lo = ""
        self._quantity_hi = ""
        self._unit = ""

        self._doc = ""
        self._parsed = False

        self.parse()

        self.process()


    def __bool__(self): return self._parsed

    def __len__(self): return self._parsed

    @property
    def doc(self): return self._doc

    @property
    def pattern(self): return self._pattern

    @property
    def snippet(self): return self._snippet

    @property
    def keyword(self): return self._keyword

    @property
    def semantic(self): return self._base_keyword

    @property
    def quantity(self): return self._quantity

    @property
    def quantity_lo(self): return self._quantity_lo

    @property
    def quantity_hi(self): return self._quantity_hi

    @property
    def unit(self): return self._unit

    @property
    def parsed(self): return self._parsed

    @property
    def var_name(self): return self._var_name

    @property
    def allowed_empty(self): return self._allowed_empty

    def parse(self):
        """Parse snippet into keyword, parameters, quantity, and unit metadata."""
        # extract keyword and raw parameter text
        keyword, params_txt = self._snippet[:-1].split("(", maxsplit=1)
        parser = ParsedKeywordMappingName(keyword)
        if not parser:
            return

        # parse parameters
        if params_txt.strip():
            for p in re.split(r"\s*,\s*", params_txt):
                p = p.strip()
                if "_" not in p:
                    continue

                if p.lower() == "or_empty":
                    self._allowed_empty = True
                    continue

                prefix, var_name = p.split("_", maxsplit=1)
                if prefix == "var":
                    self._var_name = var_name.strip()

        # assign keyword + semantic info
        self._keyword = parser.keyword
        self._base_keyword = parser.base_keyword

        # extract quantity + unit
        pattern = r"((?P<qty>optional)_)?(?P<unit>group|items)"
        quantity = parser.quantity or ""
        m = re.fullmatch(pattern, quantity)

        self._quantity = (m.group("qty") or "") if m else quantity
        self._unit = m.group("unit") if m else ""
        self._quantity_lo = parser.quantity_lo
        self._quantity_hi = parser.quantity_hi

        self._pattern = parser.pattern

        self._parsed = True

    def add_allowed_empty_note(self, items):
        """Append an allowed‑empty note when applicable."""
        if not self._allowed_empty:
            return

        mapping = {
            "anything": (
                "this semantic already matches zero characters, "
                "so the allowed‑empty flag has no effect."
            ),
            "something": (
                'enabling allowed‑empty downgrades "+" from one‑or‑more '
                'to zero‑or‑more ("*").'
            )
        }

        for keyword, description in mapping.items():
            if keyword == self._keyword:
                note = f"Note: {description}"
                if len(description) > 84:
                    note = wrap_text_block(description, subject="Note:", limit=80)
                items.append(indent(note, " " * 4))
                break

    def add_params_section(self, items):
        """Append the Parameters section if any parameters are present."""
        lines = ["Parameters"]
        if self._var_name:
            v = self._var_name
            line = f"var_{v} ({v}): capture variable using (?P<{v}>...)"
            lines.append(indent(line, " " * 4))
        if self._allowed_empty:
            line = "or_empty (True): allows the entire unit or group to be empty"
            lines.append(indent(line, " " * 4))
        lines.append("-" * 60)

        if len(lines) != 2:
            items.append(indent("\n".join(lines), "    "))

    def add_base_semantic_section(self, items):
        """Determine the base semantic token and append its documentation block."""

        # Resolve base token
        if self._keyword in ("anything", "something"):
            base = "dot"
        elif PATTERN.keyword_in(self._base_keyword, singular=True, plural=True):
            base = (
                PATTERN.resolve_plural(self._base_keyword)
                if self._unit in ("group", "items") else
                PATTERN.resolve_singular(self._base_keyword)
            )
        elif PATTERN.keyword_in(self._base_keyword, semantic=True, plural_semantic=True):
            base = PATTERN.resolve_semantic(self._base_keyword)
        else:
            base = "dot"

        # Build documentation text
        base_pattern_text = enclose_string(ElementPattern(f"{base}()"))
        base_op_doc = OperationDoc(base).doc
        line = f"Base ({base}): r{base_pattern_text} ({base_op_doc})"
        if len(line) <= 90:
            items.append(indent(line, " " * 4))
            return base
        block_doc = wrap_text_block(base_op_doc, subject="   ")
        txt = f"Base ({base}): r{base_pattern_text}\n{block_doc}"
        items.append(indent(txt, " " * 4))
        return base

    def get_semantic_group_description(self, base, quantifier=""):
        """Return the semantic description for grouped <base> patterns."""
        occurrences = "zero-or-more" if quantifier == "*" else "one-or-more"
        optional = "?" if self._allowed_empty else ""

        if self._allowed_empty:
            lst = [
                f"Semantic: (<{base}>(<sep><{base}>){quantifier}){optional}\n"
                f'    <sep> is the whitespace separator (r"\\s+")\n'
                f'    "{quantifier}" repeats {occurrences} (<sep><{base}>) groups\n'
                f'    "{optional}" accept zero or one match {base} group'
            ]
            return "\n".join(lst)

        lst = [
            f"Semantic: <{base}>(<sep><{base}>){quantifier}\n"
            f'    <sep> is the whitespace separator (r"\\s+")\n'
            f'    "{quantifier}" repeats {occurrences} (<sep><{base}>) groups'
        ]
        return "\n".join(lst)

    def get_semantic_description(self, base, quantifier="", is_group=False):
        """Return the semantic description for the given base and quantifier."""
        if is_group:
            return self.get_semantic_group_description(base, quantifier)

        if quantifier == "+" or quantifier == "*":
            quant, occurrences = (
                ("*", "zero-or-more") if self._allowed_empty else ("+", "one-or-more")
            )
        elif quantifier == "?":
            quant, occurrences = "?", "zero-or-one"
        else:
            quant, occurrences = (
                ("?", "zero-or-one") if self._allowed_empty else ("", "one")
            )

        lst = [f"Semantic: <{base}>{quant}"]
        if quant:
            lst.append(indent(f'"{quant}" repeats {occurrences} {base}', " " * 4))

        return "\n".join(lst)

    def add_custom_semantic_section(self, items):
        """Append custom semantic descriptions for 'anything' and 'something'."""
        if self._keyword not in ("anything", "something"):
            return
        quantifier = "+" if self._keyword == "something" else "*"
        desc = self.get_semantic_description("dot", quantifier=quantifier)
        items.append(indent(desc, " " * 4))

    def add_core_semantic_section(self, base, items):
        """Append the core semantic description for this keyword, if applicable."""
        if self._keyword not in PATTERN.core_keywords:
            return

        if PATTERN.keyword_in(self._keyword, singular=True, plural=True, semantic=True):
            if PATTERN.keyword_in(self._keyword, plural=True):
                desc = self.get_semantic_description(base, quantifier="+")
                items.append(indent(desc, " " * 4))
                return
            desc = self.get_semantic_description(base, quantifier="")
            items.append(indent(desc, " " * 4))
            return
        desc = self.get_semantic_description(base, quantifier="*", is_group=True)
        items.append(indent(desc, " " * 4))

    def add_semantic_section(self, items):
        """Build the full semantic section by composing base, custom, and core parts."""
        base = self.add_base_semantic_section(items)
        self.add_custom_semantic_section(items)
        self.add_core_semantic_section(base, items)

    def create_intro(self):
        """Build the introductory explanation header."""
        return [
            "Explanation:",
            indent(f"Snippet: {self.snippet}", " " * 4)
        ]

    def process(self):

        lst = self.create_intro()
        self.add_params_section(lst)
        self.add_semantic_section(lst)
        self.add_allowed_empty_note(lst)

        self._doc = "\n".join(lst) + "\n"