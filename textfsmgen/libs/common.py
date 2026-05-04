"""
textfsmgen.libs.common
======================

General-purpose common functions used across TextFSMGen.
"""  # noqa

import sys
import textwrap
import platform

from . import ECODE


def dedent_and_strip(txt):
    """Normalize text by decoding bytes, converting non-strings, and removing indentation."""
    value = (
        txt.decode("utf-8")
        if isinstance(txt, bytes)
        else txt
        if isinstance(txt, str)
        else repr(txt)
    )
    return textwrap.dedent(value).strip()


def decorate_list_of_line(items: list[str]) -> str:
    """Return a framed text block with each line padded to the longest width."""
    max_len = max(len(item) for item in items)
    border = f"+-{'-' * max_len}-+"
    rows = [f"| {item.ljust(max_len)} |" for item in items]
    return "\n".join([border] + rows + [border])


def decorate_text(text: str) -> str:
    """Decorate a block of text by converting it into line fragments."""
    raw = text.decode("utf-8") if isinstance(text, bytes) else str(text)
    if not raw.strip():
        return ""

    lines = raw.splitlines()

    # Preserve trailing newline
    if lines[-1] and (raw.endswith("\n") or raw.endswith("\r")):
        lines.append("")

    return decorate_list_of_line(lines)


def sys_exit(success: bool = True, msg: str = "") -> None:
    """Terminate the process with a standardized exit code and optional message."""
    exit_code = ECODE.SUCCESS if success else ECODE.BAD

    if msg:
        stream = sys.stderr if exit_code == ECODE.BAD else sys.stdout
        print(msg, file=stream)

    sys.exit(exit_code)


def ensure_tkinter_available(app_name: str = ""):
    """Load tkinter or exit with a formatted diagnostic message."""

    name = str(app_name).title() if app_name else "The"

    try:
        import tkinter as tk

        return tk

    except ModuleNotFoundError:
        lines = [
            f"{name} application failed to start.",
            f"Python {platform.python_version()} was detected without the tkinter module.",
            "Install tkinter to enable GUI support and retry.",
        ]
        sys_exit(False, decorate_list_of_line(lines))

    except Exception as exc:
        lines = [
            f"{name} application could not be started due to:",
            f"*** {type(exc).__name__}: {exc}",
        ]
        sys_exit(False, decorate_list_of_line(lines))
