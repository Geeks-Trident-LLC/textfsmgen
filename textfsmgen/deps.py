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
