"""
textfsmgen.__init__
===================

Top-level module for the `textfsmgen` package.

"""

from textfsmgen.core.template import LineParser
from textfsmgen.core.template import TemplateBuilder
from textfsmgen.core.template import CategoryTemplateBuilder
from textfsmgen.core.template import TableTemplateBuilder
from textfsmgen.config import version

__version__ = version

__all__ = [
    'LineParser',
    'TemplateBuilder',
    'CategoryTemplateBuilder',
    'TableTemplateBuilder',
    'version',
]
