"""
textfsmgen.__init__
===================

Top-level module for the `textfsmgen` package.

"""

from textfsmgen.core.template import LineParser
from textfsmgen.core.template import TemplateBuilder
from textfsmgen.config import version

__version__ = version

__all__ = [
    'LineParser',
    'TemplateBuilder',
    'version',
]
