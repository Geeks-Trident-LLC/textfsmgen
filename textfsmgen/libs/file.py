"""
textfsmgen.libs.file
=====================

General-purpose file functions used across TextFSMGen.
"""
import yaml

from .common import sys_exit
from textfsmgen.exceptions import raise_exception


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


def safe_load_yaml(filename: str):
    """Load YAML from a file and return the parsed object."""
    try:
        stream = read(filename)
        return yaml.safe_load(stream)
    except yaml.YAMLError as ex:
        raise_exception(ex, msg=f"Failed to parse YAML file {filename}: {ex}")
    except Exception as ex:
        raise ex
