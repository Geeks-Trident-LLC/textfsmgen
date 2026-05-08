# tester_create.py

from __future__ import annotations

import sys
from typing import List, Dict, Any

from textfsmgen.cli.tester.tester_paths import resolve_case_creation_path
from .tester_manifest_model import Manifest, load_manifest_config, write_manifest
from .tester_files import (
    create_main_case_files,
    create_non_main_case_files,
)


def handle_tester_create(argv: List[str]) -> int:
    """
    Handle `textfsmgen tester create <case> [options]` and
    `textfsmgen tester create <case> --config <file>`.
    """
    if not argv:
        print("error: missing <case>", file=sys.stderr)
        return 1

    case, *rest = argv
    flags = _parse_create_flags(rest)

    category = flags.get("category")
    builder = flags.get("builder")
    config_file = flags.get("config")

    if config_file and (category or builder):
        # flags override config, but both allowed; you can relax this if you want
        pass

    if config_file:
        manifest = load_manifest_config(config_file)
        if category:
            manifest.category = category
        if builder:
            manifest.builder = builder
    else:
        if not category or not builder:
            print("error: --category and --builder are required without --config", file=sys.stderr)
            return 1
        manifest = Manifest.from_flags(
            builder=builder,
            category=category,
            author=flags.get("author", ""),
            email=flags.get("email", ""),
            saved=flags.get("saved", False),
        )

    target_dir = resolve_case_creation_path(case, manifest.category)
    if target_dir is None:
        print("error: cannot determine creation path for case", file=sys.stderr)
        # you can print the path resolution table hint here
        return 1

    if manifest.category == "main":
        create_main_case_files(target_dir)
    else:
        create_non_main_case_files(target_dir)

    write_manifest(target_dir, manifest)

    _print_post_create_reminders(manifest)
    return 0


def _parse_create_flags(args: List[str]) -> Dict[str, Any]:
    """
    Very small flag parser for create.
    You can later replace this with argparse/click if desired.
    """
    result: Dict[str, Any] = {}
    it = iter(args)
    for token in it:
        if token == "--category":
            result["category"] = next(it, None)
        elif token == "--builder":
            result["builder"] = next(it, None)
        elif token == "--author":
            result["author"] = next(it, "")
        elif token == "--email":
            result["email"] = next(it, "")
        elif token == "--saved":
            result["saved"] = True
        elif token == "--config":
            result["config"] = next(it, None)
        else:
            print(f"warning: unknown flag {token}", file=sys.stderr)
    return result


def _print_post_create_reminders(manifest: Manifest) -> None:
    print("Created new golden test case.")
    print("Please fill in required parameters in manifest.json.")
    if manifest.meta.saved:
        print(
            "Since --saved was enabled, please update:\n"
            "  - meta.description\n"
            "  - meta.notes\n"
            "  - meta.schema_version"
        )
    print(
        "Next steps:\n"
        "  1. Edit canonical/ or expected/ snippet + template\n"
        "  2. Add input samples under inputs/\n"
        "  3. Run: pytest tests/golden --regen-golden"
    )
