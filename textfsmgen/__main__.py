"""
textfsmgen.__main__
===================

Command-line entry point for the `textfsmgen` package.

This module enables direct execution of `textfsmgen` via the command line.
It parses arguments, initializes the environment, and invokes the core
functions for generating and validating TextFSM templates.

Contents
--------
- Argument parsing for CLI options
- Dispatch to template generation and validation routines
- Error handling and exit code management
- Integration with package constants and utilities

Usage
-----
Run the package directly to access CLI functionality:

    $ python -m textfsmgen --input patterns.yaml --output template.fsm

Or, if installed as a script:

    $ textfsmgen --input patterns.yaml --output template.fsm

Notes
-----
- This module is not intended for import in application code.
- It provides a user-facing interface for template generation and
  validation, complementing the programmatic API exposed in
  `textfsmgen.__init__`.
"""

from textfsmgen.main import Cli

console = Cli()
console.run()
