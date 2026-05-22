"""
textfsmgen.libs.common
=====================

General-purpose generic classes used across TextFSMGen.
"""

import re


from typing import Any, Mapping, Iterable


class DotDict(dict):
    """
    Dictionary with attribute-style access, normalization, and safe shadowing rules.
    """

    _valid_attr = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

    _reserved = (
        set(dir(dict))
        | set(dir(object))
        | {
            "_valid_attr",
            "_reserved",
            "_wrap",
            "from_mapping",
            "from_pairs",
            "_find_normalized_key",
        }
    )

    # ------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "DotDict":
        obj = cls()
        for k, v in mapping.items():
            obj[k] = cls._wrap(v)
        return obj

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[str, Any]]) -> "DotDict":
        obj = cls()
        for k, v in pairs:
            obj[k] = cls._wrap(v)
        return obj

    @staticmethod
    def _wrap(value: Any) -> Any:
        if isinstance(value, dict) and not isinstance(value, DotDict):
            return DotDict.from_mapping(value)
        if isinstance(value, list):
            return [DotDict._wrap(v) for v in value]
        if isinstance(value, tuple):
            return tuple(DotDict._wrap(v) for v in value)
        return value

    # ------------------------------------------------------------
    # Normalization helper (used for both get + set)
    # ------------------------------------------------------------
    def _find_normalized_key(self, name: str) -> str | None:
        """
        Return the actual dict key that corresponds to attribute name.
        """
        # Direct match
        if name in self:
            return name

        # Trailing underscore shadowing
        if name.endswith("_"):
            base = name[:-1]
            if base in self:
                return base

        # Normalization attempts
        candidates = (
            name.replace("_", " ").strip(),
            name.replace("_", ".").strip("."),
            name.replace("_", "-").strip("-"),
        )
        for key in candidates:
            if key in self:
                return key

        return None

    # ------------------------------------------------------------
    # Attribute access
    # ------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        if not self._valid_attr.fullmatch(name):
            raise AttributeError(
                f"Invalid attribute name {name!r}. Expected pattern "
                f"{self._valid_attr.pattern!r}."
            )

        key = self._find_normalized_key(name)
        if key is not None:
            return self._wrap(self[key])

        raise AttributeError(f"Invalid attribute name {name!r}.")

    # ------------------------------------------------------------
    # Attribute assignment
    # ------------------------------------------------------------
    def __setattr__(self, name: str, value: Any) -> None:
        # Internal attributes
        if (
            name.startswith("_")
            or name in self._reserved
            or name in type(self).__dict__
        ):
            object.__setattr__(self, name, value)
            return

        # Try to find normalized key
        key = self._find_normalized_key(name)
        if key is not None:
            self[key] = self._wrap(value)
            return

        # Otherwise create new key using attribute name
        self[name] = self._wrap(value)

    # ------------------------------------------------------------
    # Dict overrides
    # ------------------------------------------------------------
    def __setitem__(self, key: str, value: Any) -> None:
        super().__setitem__(key, self._wrap(value))

    def update(self, *args, **kwargs) -> None:
        for k, v in dict(*args, **kwargs).items():
            self[k] = v


class StatusString(str):
    """String value carrying a boolean status and optional reason."""

    _ALLOWED_TRUE = {
        # Boolean‑like
        "true",
        "yes",
        "y",
        "ok",
        "okay",
        "checked",
        "on",
        # Success / pass states
        "pass",
        "passed",
        "success",
        "successful",
        "good",
        "valid",
        "correct",
        "accepted",
        "approved",
        "validated",
        "verified",
        "ready",
        "parsed",
        "matched",
        "resolved",
        # Completion states
        "done",
        "complete",
        "completed",
    }

    def __new__(cls, *args, **kwargs):
        text = (
            args[0]
            if args
            else kwargs.pop("text", kwargs.pop("data", kwargs.pop("value", "")))
        )

        status = args[1] if len(args) > 1 else kwargs.pop("status", False)

        reason = (
            args[2]
            if len(args) > 2
            else kwargs.pop("reason", kwargs.pop("message", ""))
        )

        # Remove consumed kwargs
        for key in ("text", "data", "value", "status", "reason", "message"):
            kwargs.pop(key, None)

        obj = super().__new__(cls, text, **kwargs)
        obj.raw = text
        obj.status = str(status).strip().lower() in cls._ALLOWED_TRUE
        obj.error = str(status).strip().lower()
        obj.reason = str(reason)
        return obj

    def __bool__(self):
        return self.status

    def is_good(self):
        return self.status is True

    def is_bad(self):
        return self.status is False

    def is_success(self):
        return self.status is True

    def is_failure(self):
        return self.status is False


class Position:
    """Simple counter that tracks a numeric position."""

    def __init__(self, value: int = 0):
        self.value = int(value)

    def increment(self) -> int:
        """Increase the position by one and return the new value."""
        self.value += 1
        return self.value

    def current(self):
        """Get the current position."""
        return self.value

    def next(self):
        """Increase the position by one and return the new value."""
        self.value += 1
        return self.value

    def reset(self):
        """Reset the position."""
        self.value = 0
        return self.value
