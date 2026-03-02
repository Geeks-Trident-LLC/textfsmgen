"""
textfsmgen.__init__
===================

Top-level module for the `textfsmgen` package.

"""

from textfsmgen.core import ParsedLine
from textfsmgen.core import TemplateBuilder
from textfsmgen.config import version

__version__ = version

__all__ = [
    'ParsedLine',
    'TemplateBuilder',
    'version',
]
