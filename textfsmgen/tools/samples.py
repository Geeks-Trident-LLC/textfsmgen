"""
textfsmgen.tools.samples
========================

Utilities for generating random test samples used in TextFSM verification and testing.
"""

import random
import re

from textfsmgen.libs.pattern import ParsedKeywordMappingName, PATTERN

from textfsmgen.core.patterns import LinePattern

from textfsmgen.tools.samples_data import (
    letter_samples, letters_samples,
    alnum_samples, alnums_samples,
    graph_samples, graphs_samples,
    punct_samples, puncts_samples,
    word_samples, mixed_word_samples,
    digit_samples, digits_samples,
    non_ws_samples, non_wss_samples,
    space_samples, spaces_samples,
    ws_samples, wss_samples,
    dot_samples, dots_samples,
)


def generate_number_samples(count=1000, prefix="", suffix=""):
    """Return up to `count` formatted random numbers derived from item/divisor."""
    count = max(count, 10)
    total = count * 2

    samples = []
    for item in range(total):
        divisor = random.randint(total // 8, total // 4)
        result = item / divisor
        formatted = f"{prefix}{result:.2f}{suffix}"

        if formatted not in samples:
            samples.append(formatted)
    random.shuffle(samples)
    return samples[:count]


def generated_mixed_number_samples(count=1000):
    """Return `count` mixed numeric samples with various prefix/suffix patterns."""
    base = generate_number_samples(count)
    samples = list(base)

    patterns = [
        ("+", ""),   # +123
        ("-", ""),   # -123
        ("$", ""),   # $123
        ("", "%"),   # 123%
        ("(", ")"),  # (123)
    ]

    slice_size = count // 4

    for prefix, suffix in patterns:
        mixed = generate_number_samples(count, prefix=prefix, suffix=suffix)
        random.shuffle(mixed)
        samples.extend(mixed[:slice_size])

    random.shuffle(samples)
    return samples[:count]


def shuffled_copy(items):
    """Return a shuffled copy of the given list."""
    result = items.copy()
    random.shuffle(result)
    return result


class SamplesGenerator:
    def __init__(self, snippet, count=3):
        self._snippet = snippet.strip()
        self._count = count

        self._is_parsed = False
        self._allowed_empty = False
        self._parser = None

        self._number_samples = generate_number_samples()
        self._mixed_number_samples = generated_mixed_number_samples()

        self._mapping= {
            "dot": dot_samples,             "dots": dots_samples,
            "space": space_samples,         "spaces": spaces_samples,

            "digit": digit_samples,         "digits": digits_samples,

            "number": self._number_samples,
            "mixed_number": self._mixed_number_samples,

            "letter": letter_samples,       "letters": letters_samples,
            "alnum": alnum_samples,         "alnums": alnums_samples,
            "graph": graph_samples,         "graphs": graphs_samples,

            "punct": punct_samples,         "puncts": puncts_samples,
            "punctuation": punct_samples,   "punctuations": puncts_samples,

            "word": word_samples,
            "mixed_word": mixed_word_samples,

            "ws": ws_samples,               "wss": wss_samples,
            "whitespace": ws_samples,       "whitespaces": wss_samples,

            "non_ws": non_ws_samples,       "non_whitespace": non_ws_samples,
            "non_wss": non_wss_samples,     "non_whitespaces": non_wss_samples,
        }

        self.update_allowed_empty()
        self.parse()

    def __bool__(self): return self._is_parsed

    def __len__(self): return 1 if self._is_parsed else 0

    @property
    def pattern(self): return LinePattern(self._snippet) if self else ""

    def update_allowed_empty(self):
        keyword, remainder = self._snippet.split("(")
        self._allowed_empty = any(
            re.match("or_empty", item)
            for item in re.split(",", remainder)
        )

    def parse(self):

        if not self._snippet or not re.fullmatch(r"\w+[(][^)]*[)]", self._snippet):
            return

        keyword, remainder = self._snippet.split("(")

        parser = ParsedKeywordMappingName(keyword)
        if not parser:
            return

        self._parser = parser
        base_keyword = parser.base_keyword

        if base_keyword not in PATTERN.core_keywords:
            if keyword not in ("anything", "something"):
                return
        self._is_parsed = True

    def get_sample(self, keyword, total=None):
        if keyword in self._mapping:
            samples = self._mapping[keyword].copy()
            if total is None or isinstance(total, int) and len(samples) > total:
                random.shuffle(samples)
                return samples
            for _ in range(1000):
                samples.extend(samples[:])
                if len(samples) > total:
                    random.shuffle(samples)
                    return samples
        return []

    def create_sample_group(self, keyword, starting=1, ending=None, exact=None):
        """Return grouped samples for the given keyword."""
        if keyword not in self._mapping:
            return []

        count = self._count

        # --- Exact mode ---------------------------------------------------------
        if exact is not None:
            if not exact:
                return []

            values = self.get_sample(keyword, total=exact)

            parts = []
            for _ in range(count):
                random.shuffle(values)
                parts.append(" ".join(values[:exact]))
            return parts

        # --- Range mode ---------------------------------------------------------
        ending = ending if ending and ending > starting else starting + 4
        values = self.get_sample(keyword, total=ending)
        parts = []
        for _ in range(count):
            random.shuffle(values)
            size = random.randint(starting, ending)
            parts.append(" ".join(values[:size]))
        return parts

    def generate_core(self):
        keyword = self._parser.keyword
        if keyword in ("anything", "something"):
            self._allowed_empty = keyword == "anything"
            keyword = "dots"
        return self.get_sample(keyword)[:self._count]

    def generate_plural_semantic(self):
        keyword = self._parser.keyword
        if PATTERN.keyword_in(keyword, plural_semantic=True):
            semantic = PATTERN.resolve_semantic(keyword)
            return self.create_sample_group(semantic, starting=1)
        return []

    def generate_some(self):
        """Generate samples for 'some', 'one_or_more', or 'zero_or_more' quantities."""
        qty = self._parser.quantity

        # Only these quantities are supported
        if qty not in ("some", "one_or_more", "zero_or_more"):
            return []

        # zero_or_more allows empty output
        if qty == "zero_or_more":
            self._allowed_empty = True

        base = self._parser.base_keyword

        # --- Singular / plural keyword path -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True):
            resolved = PATTERN.resolve_plural(base)
            return self.get_sample(resolved)[: self._count]

        # --- Semantic / plural semantic path ------------------------------------
        if PATTERN.keyword_in(base, semantic=True, plural_semantic=True):
            semantic = PATTERN.resolve_semantic(base)
            return self.create_sample_group(semantic, starting=1)

        return []

    def generate_optional(self):
        qty = self._parser.quantity

        # Only these quantities are supported
        if qty not in ("optional", "zero_or_one"):
            return []

        # # zero_or_more allows empty output
        # if qty == "zero_or_one":
        self._allowed_empty = True

        base = self._parser.base_keyword

        # --- Singular / plural keyword path -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True, semantic=True):
            # self._allowed_empty = True
            return self.get_sample(base)[: self._count]

        # --- Semantic / plural semantic path ------------------------------------
        if PATTERN.keyword_in(base, plural_semantic=True):
            semantic = PATTERN.resolve_semantic(base)
            return self.create_sample_group(semantic, starting=1)

        return []

    def generate_group(self):
        qty = self._parser.quantity
        # Only these quantities are supported
        if qty not in ("optional_group", "group", "optional_items", "items"):
            return []
        self._allowed_empty = qty.startswith("optional_")
        base = self._parser.base_keyword

        # --- Singular / plural keyword path -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True):
            plural = PATTERN.resolve_plural(base)
            starting = 2 if qty == "group" else 1
            return self.create_sample_group(plural, starting=starting)

        # --- Semantic / plural semantic path ------------------------------------
        if PATTERN.keyword_in(base, semantic=True, plural_semantic=True):
            semantic = PATTERN.resolve_semantic(base)
            return self.create_sample_group(semantic, starting=1)

        return []

    def generate_exact(self):
        qty = str(self._parser.quantity)

        # Only these quantities are supported
        if not qty.isdigit():
            return []

        qty = int(qty)

        base = self._parser.base_keyword

        # --- Singular / plural keyword path -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True):
            singular = PATTERN.resolve_singular(base)
            parts = []
            for _ in range(self._count):
                part = "".join(self.get_sample(singular, total=qty))[:qty]
                parts.append(part)
            return parts

        # --- Semantic / plural semantic path ------------------------------------
        if PATTERN.keyword_in(base, semantic=True, plural_semantic=True):
            semantic = PATTERN.resolve_semantic(base)
            return self.create_sample_group(semantic, exact=qty)

        return []

    def generate_range(self):
        lo, hi = str(self._parser.quantity_lo), str(self._parser.quantity_hi)

        # Only these quantities are supported
        if not lo.isdigit() and not hi.isdigit():
            return []

        lo = int(lo) if lo.isdigit() else 0
        hi = int(hi) if hi.isdigit() else lo + 4

        base = self._parser.base_keyword

        # --- Singular / plural keyword path -------------------------------------
        if PATTERN.keyword_in(base, singular=True, plural=True):
            singular = PATTERN.resolve_singular(base)
            parts = []
            for i in range(lo, hi + 1):
                part = "".join(self.get_sample(singular, total=hi))[:i]
                if part and part not in parts:
                    parts.append(part)
            return parts[:self._count]

        # --- Semantic / plural semantic path ------------------------------------
        if PATTERN.keyword_in(base, semantic=True, plural_semantic=True):
            semantic = PATTERN.resolve_semantic(base)
            return self.create_sample_group(semantic, starting=lo, ending=hi)
        return []

    def generate(self):
        """Return the first non-empty result from available generators."""
        for func in (
            self.generate_core, self.generate_some, self.generate_optional,
            self.generate_plural_semantic,
            self.generate_group, self.generate_exact, self.generate_range,

        ):
            result = func()
            if result:
                if self._allowed_empty:
                    if "" not in result:
                        result.insert(random.randint(0, len(result)), "")
                return result
        return []
