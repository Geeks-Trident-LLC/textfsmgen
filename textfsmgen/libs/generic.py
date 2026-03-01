"""
textfsmgen.libs.common
=====================

General-purpose generic classes used across TextFSMGen.
"""

import re


class DotObject(dict):
    """Dictionary with dot-access for valid keys and recursive wrapping."""

    _valid_key = re.compile(r"_{,2}[A-Za-z][A-Za-z0-9_]*")
    _dict_members = dir(dict) + ["_valid_key", "_dict_members", "_wrap", "__getattr__"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name in self._dict_members:
            return super().__getattribute__(name)
        if name in self and self._valid_key.fullmatch(name):
            return self._wrap(self[name])
        raise AttributeError(
            f"Invalid attribute name {name!r}. Expected attribute "
            f"matching pattern {self._valid_key.pattern!r}."
        )

    def _wrap(self, value):
        """Wrap nested dictionaries into DotDict."""
        if isinstance(value, dict) and not isinstance(value, self.__class__):
            return self.__class__(value)
        return value
