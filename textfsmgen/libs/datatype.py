"""
textfsmgen.libs.datatype
========================

Utility functions for runtime type checking and data handling.
"""

from collections import abc
import copy as _copy


def is_dict(obj: object) -> bool:
    """Return True if obj is a dict."""
    return isinstance(obj, dict)


def is_mapping(obj: object) -> bool:
    """Return True if obj implements mapping protocol."""
    return isinstance(obj, abc.Mapping)


def is_list(obj: object) -> bool:
    """Return True if obj is a list."""
    return isinstance(obj, list)


def is_mutable_sequence(obj: object) -> bool:
    """Return True if obj is a mutable sequence."""
    return isinstance(obj, abc.MutableSequence)


def is_sequence(obj: object) -> bool:
    """Return True if obj is a sequence."""
    return isinstance(obj, abc.Sequence)


def is_class(obj: object) -> bool:
    """Return True if obj is a class."""
    return isinstance(obj, type)


def is_callable(obj: object) -> bool:
    """Return True if obj is callable."""
    return callable(obj)


def is_iterator(obj: object) -> bool:
    """Return True if obj is an iterator."""
    return isinstance(obj, abc.Iterator)


def is_generator(obj: object) -> bool:
    """Return True if obj is a generator."""
    return isinstance(obj, abc.Generator)


def is_iterable(obj: object) -> bool:
    """Return True if obj is iterable."""
    return isinstance(obj, abc.Iterable)


def is_none(obj: object) -> bool:
    """Return True if obj is None."""
    return obj is None


def get_class_name(obj: object) -> str:
    """Return class name of obj or class itself."""
    return obj.__name__ if is_class(obj) else type(obj).__name__


def copy_obj(obj: object, deep: bool = True) -> object:
    """Return a shallow or deep copy of obj."""
    return _copy.deepcopy(obj) if deep else _copy.copy(obj)


def clean_list_of_dicts(items: list, chars: str | None = None) -> list:
    """Return a cleaned copy of a list of dicts, stripping strings and copying other values."""
    if not isinstance(items, list):
        return items

    result: list = []
    for item in items:
        if isinstance(item, dict):
            cleaned_dict: dict = {}
            for key, val in item.items():
                if isinstance(val, str):
                    cleaned_dict[key] = val.strip(chars)
                elif isinstance(val, bytes):
                    cleaned_dict[key] = val.decode().strip(chars).encode()
                elif isinstance(val, list):
                    # Recursively clean nested lists of dicts
                    cleaned_dict[key] = clean_list_of_dicts(val, chars=chars)
                else:
                    cleaned_dict[key] = _copy.deepcopy(val)
            result.append(cleaned_dict)
        else:
            result.append(_copy.deepcopy(item))
    return result
