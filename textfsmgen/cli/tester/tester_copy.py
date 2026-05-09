# tester_copy.py

from __future__ import annotations

import sys
from typing import List

from textfsmgen.cli.tester.tester_paths import resolve_case_path, resolve_case_creation_path
from .tester_manifest_model import load_manifest, write_manifest
from .tester_files import (
    copy_main_authoritative_files,
    copy_non_main_authoritative_files,
)
from .tester_quicktest import run_quick_test_for_case


def handle_tester_copy(argv: List[str]) -> int:
    """
    textfsmgen tester copy author=<author> <target-case> <new-case>
    """
    if len(argv) < 3:
        print("error: usage: tester copy author=<author> <target-case> <new-case>", file=sys.stderr)
        return 1

    author_token, target_case, new_case = argv[0], argv[1], argv[2]
    if not author_token.startswith("author="):
        print("error: first argument must be author=<author>", file=sys.stderr)
        return 1

    author = author_token.split("=", 1)[1]

    target_dir = resolve_case_path(target_case)
    if target_dir is None:
        print(f"error: target case not found: {target_case}", file=sys.stderr)
        return 1

    manifest = load_manifest(target_dir)
    manifest.meta.author = author
    manifest.meta.saved = False
    manifest.meta.description = ""
    manifest.meta.notes = ""

    new_dir = resolve_case_creation_path(new_case, manifest.category)
    if new_dir is None:
        print("error: cannot determine creation path for new case", file=sys.stderr)
        return 1

    if manifest.category == "main":
        copy_main_authoritative_files(src=target_dir, dst=new_dir)
    else:
        copy_non_main_authoritative_files(src=target_dir, dst=new_dir)

    write_manifest(new_dir, manifest)

    run_quick_test_for_case(new_dir)

    print(f"Copied case '{target_case}' to '{new_case}' with author='{author}'.")
    return 0
