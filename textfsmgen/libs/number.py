"""
textfsmgen.libs.number
======================

Utility functions for identifying and safely converting objects into numeric
types (boolean, integer, float).
"""     # noqa

from copy import deepcopy
from typing import Any, Optional, Tuple, Type
import re


def is_boolean(obj: Any, allowed_str: bool = True) -> bool:
    """Check whether the given object represents a boolean value."""
    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()
        return bool(re.match(r"^(true|false|[+-]?0(\.0+)?|[+]?1(\.0+)?)$", text))

    if isinstance(data, (int, float, bool)):
        return data in (0, 1)

    return False


def is_integer(obj: Any, allowed_str: bool = True) -> bool:
    """Check whether the given object represents an integer value."""
    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()
        return bool(re.match(r"^(true|false|[+-]?\d+)$", text))

    return isinstance(data, (int, bool))


def is_float(obj: Any, allowed_str: bool = True) -> bool:
    """Check whether the given object represents a floating-point value."""
    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()
        return bool(re.match(r"^(true|false|[+-]?((\d+\.?\d*)|(\d*\.?\d+)))$", text))

    return isinstance(data, (int, float, bool))


def is_number(obj: Any, allowed_str: bool = True) -> bool:
    """
    Check whether the given object represents any numeric type (boolean, integer, or float).
    """
    return (
        is_boolean(obj, allowed_str=allowed_str)
        or is_integer(obj, allowed_str=allowed_str)
        or is_float(obj, allowed_str=allowed_str)
    )


def try_to_get_number(
    obj: Any, return_type: Optional[Type] = None, allowed_str: bool = True
) -> Tuple[bool, Any]:
    """Attempt to convert an object into a numeric or boolean value."""

    def cast_to_type(value: Any, target_type: Optional[Type]) -> Any:
        """Cast value to the requested type if valid, otherwise return unchanged."""
        if target_type in (int, float, bool):
            return target_type(value)
        return value

    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()

        if text in ("true", "false"):
            return True, cast_to_type(text == "true", return_type)
        if re.match(r"^[+-]?\d+$", text):
            return True, cast_to_type(int(text), return_type)
        if re.match(r"^[+-]?((\d+\.?\d*)|(\d*\.?\d+))$", text):
            return True, cast_to_type(float(text), return_type)

    if isinstance(data, (int, float, bool)):
        return True, cast_to_type(data, return_type)

    return False, obj


def word_to_digit(text, as_str: bool = True):
    """Convert a spelled-out number into its digit form when possible."""
    word = str(text).lower().strip()

    base = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19,
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    }

    if word.isdigit():
        return str(text) if as_str else int(word)

    if word in base:
        val = base[word]
        return str(val) if as_str else val

    tens = ["twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"]

    for prefix in tens:
        if word.startswith(prefix):
            suffix = word[len(prefix):].strip("_-")
            if suffix in base:
                val = base[prefix] + base[suffix]
                return str(val) if as_str else val

    return text


def digit_to_word(value):
    """Convert a numeric value into its English word form when possible."""
    text = str(value).lower().strip()

    ok, num = try_to_get_number(text, return_type=int)
    if not ok:
        return value

    # Base words for 0–90
    base = {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
        5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
        14: "fourteen", 15: "fifteen", 16: "sixteen",
        17: "seventeen", 18: "eighteen", 19: "nineteen",
        20: "twenty", 30: "thirty", 40: "forty", 50: "fifty",
        60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety",
    }

    # Direct mapping for base numbers
    if num in base:
        return base[num]

    # Handle 21–99 (tens + hyphen + ones)
    tens, ones = divmod(num, 10)
    tens_word = base.get(tens * 10)
    ones_word = base.get(ones)

    if tens_word and ones_word:
        return f"{tens_word}-{ones_word}"

    return str(num)
