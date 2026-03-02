"""
textfsmgen.libs.number
======================

Utility functions for identifying and safely converting objects into numeric
types (boolean, integer, float).
"""

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