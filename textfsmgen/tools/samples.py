"""
textfsmgen.tools.samples
========================

Utilities for generating random test samples used in TextFSM verification and testing.
"""

import string
import random
import re

from textfsmgen.libs.pattern import ParsedKeywordMappingName, PATTERN

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
        self.snippet = snippet.strip()
        self.count = count

        self.is_parsed = False
        keyword, remainder = snippet.split("(")

        self.allowed_empty = any(re.match("or_empty", item) for item in re.split(",", remainder))

        self.keyword = ""
        self.base_keyword = ""
        self.pattern = ""
        self.quantity = ""
        self.quantity_lo = ""
        self.quantity_hi = ""

        self.number_samples = generate_number_samples()
        self.mixed_number_samples = generated_mixed_number_samples()

        self.mapping = self.get_mapping()

        self.parse()

    def __bool__(self): return self.is_parsed

    def __len__(self): return 1 if self.is_parsed else 0

    def parse(self):

        if not self.snippet or not re.fullmatch(r"\w+[(][^)]*[)]", self.snippet):
            return

        keyword, remainder = self.snippet.split("(")

        node = ParsedKeywordMappingName(keyword)
        if not node:
            return

        self.keyword = node.keyword
        self.base_keyword = node.base_keyword
        self.quantity = node.quantity
        self.quantity_lo = node.quantity_lo
        self.quantity_hi = node.quantity_hi
        self.pattern = node.pattern

        if self.base_keyword not in PATTERN.core_keywords:
            if self.keyword not in ("anything", "something"):
                return
        self.is_parsed = True

    def get_mapping(self):
        mapping = {
            "dot": dot_samples,             "dots": dots_samples,
            "space": space_samples,         "spaces": spaces_samples,

            "digit": digit_samples,         "digits": digits_samples,

            "number": self.number_samples,
            "mixed_number": self.mixed_number_samples,

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
        return mapping

    def generate_custom(self):
        if self.keyword not in ("anything", "something"):
            return []

        values = self.mapping.get("dots").copy()
        random.shuffle(values)
        self.allowed_empty = self.keyword == "anything"
        return values[:self.count]

    def generate_core(self):
        """Return shuffled samples for this keyword or an empty list."""
        values = self.mapping.get(self.keyword)
        if not values:
            return []

        result = values.copy()
        random.shuffle(result)
        return result[:self.count]

    def generate(self):
        """Return the first non-empty result from available generators."""
        for func in (
            self.generate_custom, self.generate_core,
        ):
            result = func()
            if result:
                if self.allowed_empty:
                    result.insert(1, '')
                return result
        return []
