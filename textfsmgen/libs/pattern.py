"""
textfsmgen.libs.pattern
=======================

General-purpose Patter class and functions used across TextFSMGen.
"""     # noqa

import re
import string

from textfsmgen.exceptions import (
    raise_exception,
    raise_runtime_error,
    EscapePatternError,
)
from .generic import StatusString, DotObject
from .number import word_to_digit


class KeywordPatternMappingRegister:
    def __init__(self):
        self.singular_keywords = None
        self.singular_map = None

        self.plural_keywords = None
        self.plural_map = None

        self.semantic_keywords = None
        self.semantic_map = None

        self.plural_semantic_keywords = None
        self.plural_semantic_map = None

        self.group_keywords = None
        self.group_map = None

        self.items_map = None
        self.items_keywords = None

        self.core_keywords = None
        self.core_map = None

        self.all_keywords = None
        self.all_map = None

        self.singular_to_plural = dict()
        self.plural_to_singular = dict()
        self.semantic_to_plural_semantic = dict()
        self.plural_semantic_to_semantic = dict()

        self.init()

    def init(self):
        self.init_singular()
        self.init_plural()
        self.init_semantic()
        self.init_plural_semantic()

        self.core_map = self.singular_map.copy()
        self.core_map.update(self.plural_map.copy())
        self.core_map.update(self.semantic_map.copy())
        self.core_map.update(self.plural_semantic_map.copy())

        self.core_keywords = list(self.core_map.keys())

        self.all_map = self.build_all()
        self.all_keywords = list(self.all_map.keys())

        self.group_map = dict()
        self.group_keywords = []

        self.items_map = dict()
        self.items_keywords = []

        for keyword in self.core_keywords:
            grp_keyword = f"{keyword}_group"
            if grp_keyword in self.all_map:
                self.group_map[grp_keyword] = self.all_map[grp_keyword]
                self.group_keywords.append(grp_keyword)

            items_keyword = f"{keyword}_items"
            if items_keyword in self.all_map:
                self.items_map[items_keyword] = self.all_map[items_keyword]
                self.items_keywords.append(items_keyword)

    def init_singular(self):

        punct_pat = r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
        space_or_punct_pat = r"[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
        letter_or_punct_pat = r"[a-zA-Z\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"

        self.singular_map = {
            "dot"           : ".",

            "space"         : " ",
            "ws"            : r"\s",
            "whitespace"    : r"\s",

            "digit"         : r"\d",
            "letter"        : r"[a-zA-Z]",

            "alnum"         : r"[a-zA-Z0-9]",

            "punct"         : punct_pat,
            "punctuation"   : punct_pat,

            "graph"         : r"[\x21-\x7e]",

            "non_ws"        : r"\S",
            "non_whitespace": r"\S",

            "sop"                   : space_or_punct_pat,
            "pos"                   : space_or_punct_pat,
            "space_or_punct"        : space_or_punct_pat,
            "punct_or_space"        : space_or_punct_pat,

            "lop"                   : letter_or_punct_pat,
            "pol"                   : letter_or_punct_pat,
            "letter_or_punct"       : letter_or_punct_pat,
            "punct_or_letter"       : letter_or_punct_pat,
        }

        self.singular_keywords = list(self.singular_map.keys())

    def init_plural(self):
        self.plural_keywords = []
        self.plural_map = dict()
        for keyword, pattern in self.singular_map.items():
            key = f"{keyword}s"
            # Preserve 'non_' prefix before pluralizing
            if not key.startswith("non_") and "_" in key:
                prefix, rest = key.split("_", maxsplit=1)
                key = f"{prefix}s_{rest}"
            self.plural_keywords.append(key)
            self.plural_map[key] = rf"{pattern}+"

            self.singular_to_plural[keyword] = key
            self.plural_to_singular[key] = keyword

    def init_semantic(self):
        self.semantic_map = {
            "word": r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*",
            "mixed_word": r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*",
            "number": r"\d*[.]?\d+",
            "mixed_number": r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*",
        }
        self.semantic_keywords = list(self.semantic_map.keys())

    def init_plural_semantic(self):
        self.plural_semantic_map = dict()
        self.plural_semantic_keywords = []
        sep = r"\s+"
        for keyword, pattern in self.semantic_map.items():
            self.plural_semantic_keywords.append(f"{keyword}s")
            self.plural_semantic_map[f"{keyword}s"] = rf"{pattern}({sep}{pattern})*"

            self.semantic_to_plural_semantic[keyword] = f"{keyword}s"
            self.plural_semantic_to_semantic[f"{keyword}s"] = keyword

    def build_singular_variants(self) -> dict:
        """Return expanded regex variants for each singular token pattern."""
        variants = {}
        sep = r"\s+"

        special_case = ("dot", "space", "ws", "whitespace")

        for key, pattern in self.singular_map.items():
            name = key.lower()

            # base
            variants[name] = pattern

            # zero or one
            variants[f"optional_{name}"] = f"{pattern}?"
            variants[f"zero_or_one_{name}"] = f"{pattern}?"

            # (zero or more) or (one or more)
            variants[f"some_{name}"] = f"{pattern}+"
            variants[f"zero_or_more_{name}"] = f"{pattern}*"
            variants[f"one_or_more_{name}"] = f"{pattern}+"

            # <singular>_group: represents two or more plural units
            # separated by whitespace.
            # Special cases (dot, space, whitespace) expand only to
            # their plural form, not to whitespace‑separated multi‑unit groups.
            variants[f"{name}_group"] = (
                f"{pattern}+"
                if key in special_case else
                f"{pattern}+({sep}{pattern}+)+"
            )

            # optional_<singular>_group: represents zero or more plural
            # units separated by whitespace.
            # Special cases (dot, space, whitespace) reduce to zero or more
            # of the singular token.
            variants[f"optional_{name}_group"] = (
                f"{pattern}*"
                if key in special_case else
                f"({pattern}+({sep}{pattern}+)+)?"
            )

            # <singular>_items: represents one or more plural
            # units separated by whitespace.
            # Special cases (dot, space, whitespace) expand only to
            # their plural form, not to whitespace‑separated multi‑unit groups.
            variants[f"{name}_items"] = (
                f"{pattern}+"
                if key in special_case else
                f"{pattern}+({sep}{pattern}+)*"
            )

            # optional_<singular>_items: represents zero or more plural
            # units separated by whitespace.
            # Special cases (dot, space, whitespace) become zero more unit.
            variants[f"optional_{name}_items"] = (
                f"{pattern}*"
                if key in special_case else
                f"({pattern}+({sep}{pattern}+)*)?"
            )

        return variants

    def build_plural_variants(self) -> dict:
        """Return expanded regex variants for each plural token pattern."""
        variants = {}
        sep = r"\s+"

        special_case = ("dots", "spaces", "wss", "whitespaces")

        for key, pattern in self.plural_map.items():
            name = key.lower()

            # base
            variants[name] = pattern

            # (zero or one‑of‑plural) -> zero or more of the singular unit
            variants[f"optional_{name}"] = f"{pattern[:-1]}*"
            variants[f"zero_or_one_{name}"] = f"{pattern[:-1]}*"

            # some_<plural>: one or more the singular unit
            variants[f"some_{name}"] = pattern

            # zero_or_more_<plural>: zero or more the singular unit.
            variants[f"zero_or_more_{name}"] = f"{pattern[:-1]}*"

            # one_or_more_<plural>: one or more the singular unit.
            variants[f"one_or_more_{name}"] = pattern

            # <plural>_group: two or more plural units separated by whitespace.
            variants[f"{name}_group"] = (
                f"{pattern}"
                if key in special_case else
                f"{pattern}({sep}{pattern})+"
            )

            # optional_<plural>_group: zero or more plural units separated by whitespace.
            variants[f"optional_{name}_group"] = (
                f"{pattern[:-1]}*"
                if key in special_case else
                f"({pattern}({sep}{pattern})+)?"
            )

            # <plural>_items: one or more plural units separated by whitespace.
            variants[f"{name}_items"] = (
                f"{pattern}"
                if key in special_case else
                f"{pattern}({sep}{pattern})*"
            )

            # optional_<plural>_items: zero or more plural units separated by whitespace.
            variants[f"optional_{name}_items"] = (
                f"{pattern[:-1]}*"
                if key in special_case else
                f"({pattern}({sep}{pattern})*)?"
            )

        return variants

    def build_semantic_variants(self) -> dict:
        """Return expanded regex variants for each semantic token pattern."""
        variants = {}
        sep = r"\s+"

        for key, pattern in self.semantic_map.items():
            name = key.lower()

            # base
            variants[name] = pattern

            # match zero or one semantic
            variants[f"optional_{name}"] = f"({pattern})?"
            variants[f"zero_or_one_{name}"] = f"({pattern})?"

            # some_<semantic>: one or more semantic units separated by whitespace
            variants[f"some_{name}"] = f"{pattern}({sep}{pattern})*"

            # zero_or_more_<semantic>: zero or more semantic units separated by whitespace
            variants[f"zero_or_more_{name}"] = f"({pattern}({sep}{pattern})*)?"

            # one_or_more_<semantic>: same as some_<semantic>
            variants[f"one_or_more_{name}"] = f"{pattern}({sep}{pattern})*"

            # <semantic>_group: two or more semantic units separated by whitespace
            variants[f"{name}_group"] = f"{pattern}({sep}{pattern})+"

            # optional_<semantic>_group: zero or more semantic units separated by whitespace
            variants[f"optional_{name}_group"] = f"({pattern}({sep}{pattern})+)?"

            # <semantic>_items: one or more semantic units separated by whitespace
            variants[f"{name}_items"] = f"{pattern}({sep}{pattern})*"

            # optional_<semantic>_items: zero or more semantic units separated by whitespace
            variants[f"optional_{name}_items"] = f"({pattern}({sep}{pattern})*)?"

        return variants

    def build_plural_semantic_variants(self) -> dict:
        """Return expanded regex variants for each plural semantic token pattern."""
        variants = {}
        # sep = r"\s+"

        for key, pattern in self.plural_semantic_map.items():
            name = key.lower()

            # base
            variants[name] = pattern

            # match zero or one semantic
            variants[f"optional_{name}"] = f"({pattern})?"
            variants[f"zero_or_one_{name}"] = f"({pattern})?"

            # some_<plural_semantic>: same as plural semantic
            variants[f"some_{name}"] = pattern

            # zero_or_more_<plural_semantic>: similar to optional_<plural_semantic>
            variants[f"zero_or_more_{name}"] = f"({pattern})?"

            # one_or_more_<plural_semantic>: same as plural semantic
            variants[f"one_or_more_{name}"] = pattern

            # <semantic>_group: two or more semantic units separated by whitespace
            variants[f"{name}_group"] = f"{pattern[:-1]}+"

            # optional_<plural_semantic>_group: zero or more semantic units
            # separated by whitespaces
            variants[f"optional_{name}_group"] = f"({pattern[:-1]}+)?"

            # <semantic>_items: same as plural semantic
            variants[f"{name}_items"] = pattern

            # optional_<plural_semantic>_items: zero or more semantic unit
            # separated by whitespace
            variants[f"optional_{name}_items"] = f"({pattern})?"

        return variants

    def build_all(self):
        all_map = self.build_singular_variants()
        all_map.update(self.build_plural_variants())
        all_map.update(self.build_semantic_variants())
        all_map.update(self.build_plural_semantic_variants())
        all_map.update(anything=".*")
        all_map.update(something=".+")
        return all_map


class Pattern(DotObject):
    """Reusable regex fragments for common character classes."""

    def __init__(self):
        register = KeywordPatternMappingRegister()
        kwargs = dict(zip(
            map(str.upper, register.all_keywords),  # noqa
            register.all_map.values())
        )

        super().__init__(**kwargs)

        self.singular_keywords = register.singular_keywords.copy()
        self.plural_keywords = register.plural_keywords.copy()
        self.semantic_keywords = register.semantic_keywords.copy()
        self.plural_semantic_keywords = register.plural_semantic_keywords.copy()
        self.core_keywords = register.core_keywords.copy()
        self.group_keywords = register.group_keywords.copy()
        self.items_keywords = register.items_keywords.copy()

        self.singular_to_plural = register.singular_to_plural.copy()
        self.plural_to_singular = register.plural_to_singular.copy()
        self.semantic_to_plural_semantic = register.semantic_to_plural_semantic.copy()
        self.plural_semantic_to_semantic = register.plural_semantic_to_semantic.copy()


        self.all_map = register.all_map.copy()

    @staticmethod
    def is_suppressible_group(keyword: str) -> bool:
        """Return True if keyword matches a suppressible *_group pattern."""
        bases = ("dot", "space", "ws", "whitespace")

        for base in bases:
            if keyword in (
                f"{base}_group", f"{base}s_group",
                f"{base}_items", f"{base}s_items",
            ):
                return True

        return False

    def keyword_in(
        self, key, singular=False, plural=False, semantic=False,
        plural_semantic=False, core=False, group=False, items=False,
    ):
        """Return True if the keyword belongs to any enabled keyword group."""
        pairs = [
            (singular, self.singular_keywords),
            (plural, self.plural_keywords),
            (semantic, self.semantic_keywords),
            (plural_semantic, self.plural_semantic_keywords),
            (core, self.core_keywords),
            (group, self.group_keywords),
            (items, self.items_keywords),
        ]

        for flag, keywords in pairs:
            if flag and key in keywords:
                return True
        return False

    def base_group_name(self, keyword: str) -> str:
        """Return the canonical base name for a *_group keyword."""
        # Not a group keyword → return unchanged
        if not self.keyword_in(keyword, plural_semantic=True, group=True, items=True):
            return keyword

        # Plural semantic group → singularize
        if self.keyword_in(keyword, plural_semantic=True):
            return keyword[:-1]

        base = re.sub("_(group|items)$", "", keyword)

        # Case: base itself is plural
        if self.keyword_in(base, plural=True):
            return base

        # Case: plural form of base
        plural_base = f"{base}s"
        if self.keyword_in(plural_base, plural=True):
            return plural_base

        # Case: pluralize only the first segment
        first, rest = plural_base.split("_", maxsplit=1)
        modified = f"{first}s{rest}"
        if self.keyword_in(modified, plural=True):
            return modified

        return keyword

    def parse_base_keyword(self, raw_kw: str):
        """Return the core keyword and any quantity tag extracted from a mapping name."""
        match = re.search(r"_(?P<suffix>group|items)$", raw_kw)
        suffix = match.group("suffix") if match else ""
        name = re.sub(r"_(?P<suffix>group|items)$", "", raw_kw)

        for core in self.core_keywords:
            # Case: exact match or numeric-prefixed match (e.g., "3item")
            if name == core or re.fullmatch(rf"[0-9]+{core}", raw_kw):
                qty = suffix or ""
                return StatusString(core, status="ok", reason=qty)

            prefixes = ("some", "optional", "zero_or_one",
                        "zero_or_more", "one_or_more")
            for prefix in prefixes:
                if name == f"{prefix}_{core}":
                    qty = f"optional_{suffix}" if prefix == "optional" and suffix else prefix
                    return StatusString(core, status="ok", reason=qty)

        return StatusString()

    def resolve_semantic(self, keyword):
        return self.plural_semantic_to_semantic.get(keyword, keyword)

    def resolve_plural_semantic(self, keyword):
        return self.semantic_to_plural_semantic.get(keyword, keyword)

    def resolve_plural(self, keyword):
        """Return the plural form of a singular keyword if available."""
        return self.singular_to_plural.get(keyword, keyword)

    def resolve_singular(self, keyword):
        return self.plural_to_singular.get(keyword, keyword)

    def resolve_keyword_for_pattern(self, pattern):
        """Return the keyword mapped to this pattern, preferring core keywords."""
        matches = [k for k, p in self.all_map.items() if p == pattern]

        if not matches:
            return ""

        for key in matches:
            if key in self.core_keywords:
                return key

        return matches[0]

    def allow_empty_pattern(self, pattern):
        """Return a version of the pattern that allows empty input when appropriate."""

        if pattern.endswith(")*)?") or pattern.endswith(")+)?"):
            return pattern

        keyword = self.resolve_keyword_for_pattern(pattern)

        # No keyword found → fallback: allow empty
        if not keyword:

            allowed = rf"({pattern})?"
            status = check_pattern(allowed)

            if not status:
                raise_runtime_error(
                    obj="InvalidAllowedEmptyPattern",
                    msg=(
                        "Expected a valid pattern, but received "
                        f"{allowed!r} (error: {status})"
                    )
                )
            return allowed


        if keyword in ("anything", "something"):
            return self.all_map["anything"]

        if keyword in self.core_keywords:
            return self.all_map[f"optional_{keyword}"]

        if re.match("optional_|zero_or_one_|zero_or_more_", keyword):
            return self.all_map[keyword]


        # Default allowed-empty form
        allowed = rf"({pattern})?"
        status = check_pattern(allowed)

        if not status:
            raise_runtime_error(
                obj="InvalidAllowedEmptyPattern",
                msg=(
                    "Expected a valid pattern, but received "
                    f"{allowed!r} (error: {status})"
                )
            )
        return allowed


PATTERN = Pattern()


class ParsedKeywordMappingName:
    def __init__(self, name: str, default=None):
        self._default = default
        self._name = str(name)

        self._keyword = ""
        self._base_keyword = ""
        self._pattern = ""

        self._quantity = None
        self._quantity_lo = None
        self._quantity_hi = None

        self._is_resolved = False

        self._status = StatusString()

        self.resolve()

    def __bool__(self): return self._is_resolved

    def __len__(self): return 1 if self._is_resolved else 0

    @property
    def status(self): return self._status

    @property
    def quantity(self): return self._quantity

    @property
    def quantity_lo(self): return self._quantity_lo

    @property
    def quantity_hi(self): return self._quantity_hi

    @property
    def name(self): return self._name

    @property
    def keyword(self): return self._keyword

    @property
    def base_keyword(self): return self._base_keyword

    @property
    def pattern(self): return self._pattern or PATTERN.get("non_wss_items")

    def update_base_keyword(self):
        if not self._is_resolved or self._base_keyword:
            return

        result = PATTERN.parse_base_keyword(self._name)
        if result:
            self._base_keyword = str(result)
            if not self._quantity:
                self._quantity = result.reason or None

    def set_pattern(self, pattern):
        if not pattern:
            return
        self._is_resolved = True
        self._keyword = self._name.lower()
        self._pattern = pattern

    def resolve(self) -> None:
        """Resolve this keyword by applying all pattern rules in order."""
        self.apply_defined_pattern()
        self.apply_exact()
        self.apply_range()
        self.update_base_keyword()

        if not self._is_resolved:
            msg = (f"Undefined {self._name!r} keyword.  Request technical "
                   f"support for feature extension.")
            self._status = StatusString(msg, status="unresolved")
            return
        self._status = StatusString(status="approved")

    def apply_defined_pattern(self):
        """Resolve and apply the defined pattern for this instance."""
        pattern = PATTERN.all_map.get(self._name, "")
        self.set_pattern(pattern)

    def apply_exact(self):
        """Apply an exact-count pattern when the keyword encodes a fixed quantity."""
        if self._is_resolved:
            return

        m = re.fullmatch(r"(?i)(?P<count>[0-9]+|[a-z]+)_?(?P<base>\w+)",
                         self._name)
        if not m:
            return

        raw = m.group("count").lower()
        count = word_to_digit(raw)
        base = m.group("base").lower()
        pattern = PATTERN.all_map.get(base, "")

        if not pattern or not count.isdigit():
            messages = []

            if not pattern:
                messages.append(
                    f"Undefined keyword {base!r} in {self._name}. "
                    f"Request technical support for feature extension."
                )

            if not count.isdigit():
                messages.append(
                    f"Invalid exact-count value {count!r} in keyword {self._name}."
                )

            self._status = StatusString("\n".join(messages), status=False)
            return

        # --- Case 1: singular/plural keyword -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True):
            self._quantity = str(count)
            self._base_keyword = base

            is_singular = PATTERN.keyword_in(base, singular=True)
            applied = pattern if is_singular else pattern[:-1]

            self.set_pattern(rf"{applied}{{{count}}}")
            return

        # --- Case 2: suppressible group ------------------------------------------
        if PATTERN.is_suppressible_group(base):
            self._quantity = str(count)
            self._base_keyword = PATTERN.base_group_name(base)

            self.set_pattern(rf"{pattern[:-1]}{{{count}}}")
            return

        # --- Case 3: semantic / plural-semantic groups ---------------------------
        n = max(0, int(count) - 1)
        sep = r"\s+"

        # Semantic keyword
        if PATTERN.keyword_in(base, semantic=True):
            self._quantity = str(count)
            self._base_keyword = base

            if n == 0:
                self.set_pattern(pattern)
                return

            applied = f"{pattern}({sep}{pattern})"
            self.set_pattern(rf"{applied}{{{n}}}")
            return

        # Plural-semantic group
        if PATTERN.keyword_in(base, plural_semantic=True, group=True, items=True):
            self._quantity = str(n)
            self._base_keyword = PATTERN.base_group_name(base)

            if n == 0:
                self.set_pattern(pattern)
                return

            self.set_pattern(rf"{pattern[:-1]}{{{n}}}")
            return

    def apply_range(self):
        """Apply a ranged repetition pattern when the keyword encodes a range."""
        if self._is_resolved:
            return

        m = re.fullmatch(
            r"(?i)(?P<lo_raw>[a-z0-9]*)_(to_)?(?P<hi_raw>[a-z0-9]*)_(?P<base>\w+)",
            self._name,
        )
        if not m:
            return

        sep = r"\s+"

        # --- Normalize raw bounds -------------------------------------------------
        lo_raw = m.group("lo_raw").lower() or "0"
        hi_raw = m.group("hi_raw").lower() or "999"
        hi_raw = "999" if hi_raw == "n" else hi_raw

        lo = word_to_digit(lo_raw)
        hi = word_to_digit(hi_raw)

        base = m.group("base").lower()
        pattern = PATTERN.all_map.get(base, "")

        if not pattern or not lo.isdigit() or not hi.isdigit():
            messages = []

            if not pattern:
                messages.append(
                    f"Undefined keyword {base!r} in {self._name}. "
                    f"Request technical support for feature extension."
                )

            if not lo.isdigit() or not hi.isdigit():
                messages.append(
                    f"Invalid range pair ({lo_raw}, {hi_raw}) in keyword {self._name}."
                )

            self._status = StatusString("\n".join(messages), status=False)
            return

        if int(hi) < int(lo):
            msg = (
                f"Invalid range({hi}, {lo}) in keyword {self._name}. "
                f"Expected {hi} > {lo}."
            )
            self._status = StatusString(msg, status=False)
            return

        # --- Helpers --------------------------------------------------------------
        def fmt_range(lo_val: str, hi_val: str) -> str:
            return "*" if lo_val == hi_val == "" else f"{{{lo_val},{hi_val}}}"

        def normalize_quantities(lo_val: str, hi_val: str):
            lo_norm_ = "" if lo_val == "0" else lo_val
            hi_norm_ = "" if hi_val in ("998", "999") else hi_val
            return lo_norm_, hi_norm_

        # --- Case 1: singular/plural keyword -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True):
            lo_norm, hi_norm = normalize_quantities(lo, hi)
            self._base_keyword = base
            self._quantity_lo, self._quantity_hi = str(lo_norm), str(hi_norm)

            is_singular = PATTERN.keyword_in(base, singular=True)
            applied = pattern if is_singular else pattern[:-1]
            self.set_pattern(rf"{applied}{fmt_range(lo_norm, hi_norm)}")
            return

        # --- Case 2: suppressible group ------------------------------------------
        if PATTERN.is_suppressible_group(base):
            lo_norm, hi_norm = normalize_quantities(lo, hi)
            self._base_keyword = PATTERN.base_group_name(base)
            self._quantity_lo, self._quantity_hi = normalize_quantities(lo, hi)

            self.set_pattern(rf"{pattern[:-1]}{fmt_range(lo_norm, hi_norm)}")
            return

        # --- Case 3: semantic group (shift range down by 1) -----------------------
        lo_adj = max(0, int(lo) - 1)
        hi_adj = max(0, int(hi) - 1)
        lo_s, hi_s = normalize_quantities(str(lo_adj), str(hi_adj))

        # --- Case 3a: semantic keyword -------------------------------------------
        if PATTERN.keyword_in(base, semantic=True):
            self._base_keyword = PATTERN.base_group_name(base)
            self._quantity_lo, self._quantity_hi = normalize_quantities(lo, hi)

            applied = f"{pattern}({sep}{pattern})"
            rng = fmt_range(lo_s, hi_s)

            # Optional wrapper for open‑low ranges
            if lo_s == "" and hi_s != "":
                self.set_pattern(rf"({applied}{rng})?")
                return

            self.set_pattern(rf"{applied}{rng}")
            return

        # --- Case 3b: plural semantic group ---------------------------------------
        if PATTERN.keyword_in(base, plural_semantic=True, group=True, items=True):
            self._base_keyword = PATTERN.base_group_name(base)
            self._quantity_lo, self._quantity_hi = normalize_quantities(lo, hi)

            self.set_pattern(rf"{pattern[:-1]}{fmt_range(lo_s, hi_s)}")
            return


def resolve_pattern(name, default=None):
    """Return the resolved regex pattern for the given name."""
    fallback = default or PATTERN.NON_WSS_ITEMS
    mapping = ParsedKeywordMappingName(name)
    return mapping.pattern or fallback


def resolve_keyword(name):
    """Return the normalized keyword associated with the given name."""
    mapping = ParsedKeywordMappingName(name)
    return mapping.keyword


def validate_pattern(pattern: str, flags: int = 0, exception_cls=None):
    """Compile a regex pattern or raise a custom exception."""
    exception_cls = exception_cls or Exception
    try:
        return re.compile(pattern, flags=flags)
    except re.error as ex:
        raise_exception(ex, cls=exception_cls)


def check_pattern(pattern):
    """Return a StatusString describing whether the pattern is a valid regex."""
    if not isinstance(pattern, str):
        msg = (f"Pattern must be a string, "
               f"but received <{type(pattern).__name__}:{pattern}> instead.)")
        return StatusString(msg, False)
    try:
        result = re.compile(pattern)
        return StatusString(str(result), bool(result))
    except Exception as ex:
        return StatusString(str(ex), False)


def soft_escape(pattern: str, validate: bool = True) -> str:
    """Escape only required regex metacharacters while preserving normal punctuation."""
    text = str(pattern)

    punct_or_space = string.punctuation + " "
    special_regex_chars = "^$.?*+|{}[]()\\"

    result = []
    for ch in text:
        esc = re.escape(ch)
        if ch in punct_or_space:
            result.append(esc if ch in special_regex_chars else ch)
        else:
            result.append(esc)

    escaped = "".join(result)

    if validate:
        validate_pattern(escaped, exception_cls=EscapePatternError)

    return escaped
