"""
textfsmgen.libs.file
=====================

General-purpose file functions used across TextFSMGen.
"""

from .common import sys_exit


def read(filename: str, encoding: str="utf-8"):
    """Read a text file and return its contents."""
    with open(filename, encoding=encoding) as stream:
        return stream.read()


def read_with_exit(filename: str, encoding: str="utf-8"):
    """Read a text file or terminate with a formatted error message."""
    try:
        content = read(filename, encoding=encoding)
        return content
    except Exception as ex:
        sys_exit(success=False, msg=f'*** {type(ex).__name__}: {ex}')


def write(filename: str, content: str, encoding: str="utf-8"):
    """Write text to a file, overwriting existing content."""
    with open(filename, mode="w", encoding=encoding) as stream:
        stream.write(content)
