"""Top-level module for textFSM Generator.

- allow end-user to create template or test script on GUI application.
"""

from textfsmgen.core import ParsedLine
from textfsmgen.core import TemplateBuilder
from textfsmgen.core import NonCommercialUseCls
from textfsmgen.config import version
from textfsmgen.config import edition

__version__ = version
__edition__ = edition

__all__ = [
    'ParsedLine',
    'TemplateBuilder',
    'NonCommercialUseCls',
    'version',
    'edition',
]
