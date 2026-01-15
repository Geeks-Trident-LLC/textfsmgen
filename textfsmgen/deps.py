"""
textfsmgen.deps
===============

Centralized registry for external dependency APIs used by the TextFSM Generator
framework and its integration with `regexapp`.

This module consolidates imports from external libraries (`genericlib`,
`regexapp`) into a single namespace. By exposing classes, constants, and
functions here, it provides a stable and consistent API surface for other
modules in the framework. This design reduces coupling, simplifies dependency
management, and ensures that external references are accessed through a unified
entry point.


Notes
-----
- All external dependencies should be imported and aliased here rather than
  directly in consuming modules.
- Aliases follow the convention ``<package>_<ObjectName>`` to avoid naming
  conflicts and clarify origin.
- This module is intended as a stable API surface; changes to external
  dependencies should be reflected here first.
"""

##############################
# GenericLib dependencies API
##############################

# Module imports
# Provide file and text utilities for parsing, formatting, and I/O operations.
import genericlib.file as genericlib_file_module        # noqa
import genericlib.text as genericlib_text_module        # noqa
import genericlib.number as genericlib_number_module    # noqa
import genericlib.datatype as genericlib_datatype_module    # noqa

# Core classes
# Fundamental data structures and helpers for object handling, printing, and text manipulation.
from genericlib import DotObject as genericlib_DotObject    # noqa
from genericlib import Printer as genericlib_Printer        # noqa
from genericlib import Wildcard as genericlib_Wildcard      # noqa
from genericlib import Text as genericlib_Text              # noqa
from genericlib.text import Line as genericlib_Line         # noqa

# Constant classes
# Common symbolic constants for numbers, strings, regex patterns, and indexing.
from genericlib import NUMBER as genericlib_NUMBER      # noqa
from genericlib import STRING as genericlib_STRING      # noqa
from genericlib import PATTERN as genericlib_PATTERN    # noqa
from genericlib import TEXT as genericlib_TEXT          # noqa
from genericlib import SYMBOL as genericlib_SYMBOL      # noqa
from genericlib import INDEX as genericlib_INDEX        # noqa

# Utility functions
# General-purpose helpers for text normalization, system exit, tabular data, and decorators.
from genericlib.misc import ensure_tkinter_available as genericlib_ensure_tkinter_available  # noqa
from genericlib import get_data_as_tabular as genericlib_get_data_as_tabular                 # noqa
from genericlib.text import dedent_and_strip as genericlib_dedent_and_strip                  # noqa
from genericlib.misc import sys_exit as genericlib_sys_exit                                  # noqa
from genericlib.text import decorate_list_of_line as genericlib_decorate_list_of_line        # noqa
from genericlib.constpattern import get_ref_pattern_by_name as genericlib_get_ref_pattern_by_name  # noqa
from genericlib.decorators import normalize_return_output_text as genericlib_normalize_return_output_text  # noqa

# Exception handling
# Unified error raising utilities for runtime and generic exceptions.
from genericlib.exceptions import raise_runtime_error as genericlib_raise_runtime_error  # noqa
from genericlib.exceptions import raise_exception as genericlib_raise_exception          # noqa

# Versioning
# Provides version metadata for GenericLib.
from genericlib import version as genericlib_version    # noqa


##############################
# RegexApp dependencies API
##############################

# Core pattern classes
# RegexApp abstractions for line-based, text-based, and element-based pattern definitions.
from regexapp import LinePattern as regexapp_LinePattern        # noqa
from regexapp import TextPattern as regexapp_TextPattern        # noqa
from regexapp import ElementPattern as regexapp_ElementPattern  # noqa

# Core functions
# String utilities for enclosing and formatting regex expressions.
from regexapp.core import enclose_string as regexapp_enclose_string  # noqa
