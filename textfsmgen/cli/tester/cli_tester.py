# cli_tester.py

from __future__ import annotations

import sys
from typing import Callable, Dict, List

from .tester_create import handle_tester_create
from .tester_copy import handle_tester_copy
from .tester_duplicate import handle_tester_duplicate
from .tester_run import handle_tester_run
from .tester_drift import handle_tester_drift
from .tester_preview import handle_tester_preview
from .tester_diff import handle_tester_diff
from .tester_manifest import handle_tester_edit_manifest, handle_tester_set
from .tester_regen import handle_tester_regen, handle_tester_regen_all
from .tester_maintenance import (
    handle_tester_validate_manifest,
    handle_tester_clean,
    handle_tester_clean_all,
)
from .tester_info import handle_tester_list, handle_tester_info

from .tester_paths import handle_tester_paths
from .tester_manifest import handle_tester_manifest
from .tester_approve import (
    handle_tester_approve_results,
    handle_tester_approve_template,
)


CommandHandler = Callable[[List[str]], int]


def _build_tester_dispatch_table() -> Dict[str, CommandHandler]:
    return {
        "list": handle_tester_list,
        "info": handle_tester_info,
        "paths": handle_tester_paths,
        "manifest": handle_tester_manifest,
        "approve-results": handle_tester_approve_results,
        "approve-template": handle_tester_approve_template,
        "create": handle_tester_create,
        "copy": handle_tester_copy,
        "duplicate": handle_tester_duplicate,
        "run": handle_tester_run,
        "drift": handle_tester_drift,
        "preview-template": handle_tester_preview,
        "preview-snippet": handle_tester_preview,
        "preview-generated-template": handle_tester_preview,
        "preview-results": handle_tester_preview,
        "diff-template": handle_tester_diff,
        "diff-snippet": handle_tester_diff,
        "diff-results": handle_tester_diff,
        "edit-manifest": handle_tester_edit_manifest,
        "set": handle_tester_set,
        "regen": handle_tester_regen,
        "regen-all": handle_tester_regen_all,
        "validate-manifest": handle_tester_validate_manifest,
        "clean": handle_tester_clean,
        "clean-all": handle_tester_clean_all,
    }


def main_tester(argv: List[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        _print_tester_usage()
        return 1

    action, *rest = argv
    dispatch = _build_tester_dispatch_table()

    handler = dispatch.get(action)
    if handler is None:
        _print_tester_usage(error=f"Unknown tester action: {action}")
        return 1

    return handler(rest)


def _print_tester_usage(error: str | None = None) -> None:
    if error:
        print(f"error: {error}", file=sys.stderr)

    print(
        "Usage:\n"
        "  textfsmgen tester <action> [args]\n\n"
        "Actions:\n"
        "  list\n"
        "  info <case>\n"
        "  create <case> [options]\n"
        "  create <case> --config <file>\n"
        "  copy author=<author> <target-case> <new-case>\n"
        "  duplicate author=<author> <target-case>\n"
        "  run <case>\n"
        "  drift <case>\n"
        "  preview-template <case>\n"
        "  preview-snippet <case>\n"
        "  preview-generated-template <case>\n"
        "  preview-results <case>\n"
        "  diff-template <case>\n"
        "  diff-snippet <case>\n"
        "  diff-results <case>\n"
        "  edit-manifest <case>\n"
        "  set <case> <field> <value>\n"
        "  regen <case>\n"
        "  regen-all\n"
        "  validate-manifest <case>\n"
        "  clean <case>\n"
        "  clean-all\n"
    )
