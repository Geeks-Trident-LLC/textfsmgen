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
import genericlib.number as genericlib_number_module    # noqa

# Core classes
# Fundamental data structures and helpers for object handling, printing, and text manipulation.
from genericlib import Wildcard as genericlib_Wildcard      # noqa

# Utility functions
# General-purpose helpers for text normalization, system exit, tabular data, and decorators.
from genericlib import get_data_as_tabular as genericlib_get_data_as_tabular                 # noqa


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
