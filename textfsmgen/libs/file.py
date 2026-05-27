"""
textfsmgen.libs.file
=====================

General-purpose file functions used across TextFSMGen.
"""  # noqa

import yaml
import pathlib
from .common import sys_exit
from textfsmgen.exceptions import raise_exception


def read(filename: str, encoding: str = "utf-8"):
    """Read a text file and return its contents."""
    with open(filename, encoding=encoding) as stream:
        return stream.read()


def read_with_exit(filename: str, encoding: str = "utf-8"):
    """Read a text file or terminate with a formatted error message."""
    try:
        content = read(filename, encoding=encoding)
        return content
    except Exception as ex:
        sys_exit(success=False, msg=f"*** {type(ex).__name__}: {ex}")


def write(filename: str, content: str, encoding: str = "utf-8"):
    """Write text to a file, overwriting existing content."""
    with open(filename, mode="w", encoding=encoding) as stream:
        stream.write(content)


def safe_load_yaml(filename: str):
    """Load YAML from a file and return the parsed object."""
    try:
        stream = read(filename)
        return yaml.safe_load(stream)
    except yaml.YAMLError as ex:
        raise_exception(ex, msg=f"Failed to parse YAML file {filename}: {ex}")
    except Exception as ex:
        raise ex


def path_name_old(value):
    if isinstance(value, pathlib.Path):
        return value.as_posix()
    return str(value).replace("\\", "/")


def path_name(value, root="", name=False, golden=True):
    """
    Normalize a path for display:
      - If name=True → return only the filename
      - If golden=True → strip everything before 'golden' (or before root if provided)
      - Otherwise → return relative path if possible
    """
    # Convert to Path if possible
    if isinstance(value, pathlib.Path) or (
        isinstance(value, str) and pathlib.Path(value).exists()
    ):
        path = pathlib.Path(value).resolve()

        if name:
            return path.name

        # Determine lookup folder
        if golden:
            lookup = root or "golden"
        else:
            lookup = root or ""

        parts = path.parts

        # Strip prefix up to lookup
        if lookup and lookup in parts:
            idx = parts.index(lookup)
            return pathlib.Path(*parts[idx + 1 :]).as_posix()

        # Fallback: return relative path if possible
        try:
            return path.relative_to(path.cwd()).as_posix()
        except Exception:
            return path.as_posix()

    # Not a path → normalize slashes
    return str(value).replace("\\", "/")
