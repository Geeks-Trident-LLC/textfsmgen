"""Top-level module for templatepro.

- allow end-user to create template or test script on GUI application.
"""

from templatepro.core import ParsedLine
from templatepro.core import TemplateBuilder
from templatepro.config import version
from templatepro.config import edition

__version__ = version
__edition__ = edition

__all__ = [
    'ParsedLine',
    'TemplateBuilder',
    'version',
    'edition',
]
