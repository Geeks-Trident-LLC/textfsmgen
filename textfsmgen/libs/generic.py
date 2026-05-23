# textfsmgen/libs/generic.py


class DotDict(dict):
    """
    Dictionary with attribute-style access.
    Nested dicts and lists of dicts are automatically wrapped.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.update(*args, **kwargs)

    # ------------------------------------------------------------
    # Attribute access
    # ------------------------------------------------------------
    def __getattr__(self, key):
        if not key.isidentifier():
            raise AttributeError(key)
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    # ------------------------------------------------------------
    # Ensure wrapping on assignment
    # ------------------------------------------------------------
    def __setitem__(self, key, value):
        super().__setitem__(key, self._wrap(value))

    # ------------------------------------------------------------
    # Ensure wrapping on update()
    # ------------------------------------------------------------
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    # ------------------------------------------------------------
    # Recursive wrapping logic
    # ------------------------------------------------------------
    @staticmethod
    def _wrap(value):
        if isinstance(value, dict):
            return DotDict(value)
        if isinstance(value, list):
            return [DotDict._wrap(v) for v in value]
        if isinstance(value, tuple):
            return tuple(DotDict._wrap(v) for v in value)
        return value


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
