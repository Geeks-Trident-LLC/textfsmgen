"""
Top-level CLI for the textfsmgen application.

This dispatcher handles commands such as:

    textfsmgen tester run <case>
    textfsmgen tester regen <case>

All tester subcommands are forwarded to TesterCLI with correct
argument forwarding using argparse.REMAINDER.
"""

from __future__ import annotations

import argparse

from textfsmgen.tester.cli import TesterCLI


class Cli:
    """
    Top-level command-line interface for textfsmgen.
    """

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def run(self) -> int:
        parser = self._build_parser()
        args = parser.parse_args()

        if not hasattr(args, "func"):
            parser.print_help()
            return 1

        return args.func(args)

    # ------------------------------------------------------------------
    # Parser construction
    # ------------------------------------------------------------------
    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="textfsmgen",
            description="TextFSM Generator CLI",
        )

        subparsers = parser.add_subparsers(
            dest="command",
            metavar="<command>",
        )

        # --------------------------------------------------------------
        # tester
        # --------------------------------------------------------------
        tester_parser = subparsers.add_parser(
            "tester",
            help="Golden test utilities",
            description="Golden test utilities",
        )

        # Capture everything after "tester"
        tester_parser.add_argument(
            "remaining",
            nargs=argparse.REMAINDER,
            help=argparse.SUPPRESS,
        )

        tester_parser.set_defaults(func=self._dispatch_tester)

        return parser

    # ------------------------------------------------------------------
    # Dispatchers
    # ------------------------------------------------------------------
    @staticmethod
    def _dispatch_tester(args: argparse.Namespace) -> int:
        """
        Forward all remaining arguments to TesterCLI.
        Example:
            textfsmgen tester run tests/main/demo
        becomes:
            ["run", "tests/main/demo"]
        """
        tester_cli = TesterCLI()
        return tester_cli.run_from_argv(args.remaining)


# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
def main() -> int:
    return Cli().run()
