"""
textfsmgen.libs.common
=====================

General-purpose generic classes used across TextFSMGen.
"""     # noqa

import re


class DotObject(dict):
    """Dictionary with dot-access for valid keys and recursive wrapping."""     # noqa

    _valid_key = re.compile(r"_{,2}[A-Za-z][A-Za-z0-9_]*")
    _dict_members = dir(dict) + ["_valid_key", "_dict_members", "_wrap", "__getattr__"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name in self._dict_members:
            return super().__getattribute__(name)

        if not self._valid_key.fullmatch(name):
            raise AttributeError(
                f"Invalid attribute name {name!r}. Expected attribute "
                f"matching pattern {self._valid_key.pattern!r}."
            )

        # Direct match
        if name in self:
            return self._wrap(self[name])

        # Allow trailing underscore for dict-member shadowing
        if name[:-1] in self._dict_members and name.endswith("_") and name[:-1] in self:
            return self._wrap(self[name[:-1]])

        # Normalization attempts
        space_key = name.replace("_", " ").strip()
        if space_key in self:
            return self._wrap(self[space_key])

        dot_key = name.replace("_", ".").strip(".")
        if dot_key in self:
            return self._wrap(self[dot_key])

        dash_key = name.replace("_", "-").strip("-")
        if dash_key in self:
            return self._wrap(self[dash_key])

        raise AttributeError(
            f"Invalid attribute name {name!r}."
        )

    def __setattr__(self, name, value):
        """Block overriding dict-backed keys; require update() instead."""
        # Built‑in DotObject attributes cannot be overridden
        if name in self._dict_members:
            raise AttributeError(
                f"Cannot override DotObject attribute {name!r}.")

        # Direct key match
        if name in self:
            self.update({name: value})
            return

        # Shadowing via trailing underscore (e.g., "key_")
        base = name[:-1]
        if name.endswith("_") and base in self._dict_members and base in self:
            self.update({base: value})
            return

        # Alternate key forms (space, dot, dash)
        for transformed in (
                name.replace("_", " ").strip(),
                name.replace("_", ".").strip("."),
                name.replace("_", "-").strip("-"),
        ):
            if transformed in self:
                self.update({transformed: value})
                return

        super().__setattr__(name, value)

    def _wrap(self, value):
        """Wrap nested dictionaries into DotDict."""
        if isinstance(value, dict) and not isinstance(value, self.__class__):
            return self.__class__(value)
        return value


class StatusString(str):
    def __new__(cls, *args, **kwargs):
        """String subclass that carries a boolean status affecting truthiness and length."""
        allowed = ["true", "pass", "passed", "good", "success"]

        txt = args[0] if args else kwargs.pop("text", "")
        status = args[1] if len(args) > 1 else kwargs.pop("status", False)

        result = super().__new__(cls, txt, **kwargs)    # noqa
        result.status = str(status).strip().lower() in allowed

        return result

    def __bool__(self): return self.status

    def __len__(self): return int(self.status)

    def is_good(self): return self.status == True

    def is_bad(self): return self.status == False

    def is_success(self): return self.status == True

    def is_failure(self): return self.status == False


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
