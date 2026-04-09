"""
textfsmgen.libs.decorators
==========================

This module provides reusable decorators that simplify common text‑processing
tasks across the codebase.
"""     # noqa

import functools
from textwrap import dedent
from typing import Callable, Any


def normalize_output(func: Callable) -> Callable:
    """Decorator that converts a function's return value into a clean, unindented string."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        result = func(*args, **kwargs)

        output = (
            result
            if isinstance(result, str)
            else result.decode("utf-8")
            if isinstance(result, bytes)
            else "\n".join(str(item) for item in result)
            if isinstance(result, (list, tuple))
            else str(result)
        )
        return dedent(output).strip()

    return wrapper


def try_and_catch(handler: Callable[[Exception], Any] = None) -> Callable:
    """Decorator that wraps a function and optionally handles raised exceptions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if handler:
                    return handler(exc)
                raise exc
        return wrapper
    return decorator
