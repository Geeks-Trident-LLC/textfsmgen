"""
textfsmgen.__init__
===================

Top-level module for the `textfsmgen` package.

"""

from textfsmgen.core.template import LineParser
from textfsmgen.core.template import TemplateBuilder
from textfsmgen.core.template import CategoryTemplateBuilder
from textfsmgen.core.template import TabularTemplateBuilder
from textfsmgen.core.verify import verify_snippet

__version__ = "0.6.2"
version = __version__

__all__ = [
    "LineParser",
    "TemplateBuilder",
    "CategoryTemplateBuilder",
    "TabularTemplateBuilder",
    "verify_snippet",
    "version",
]
