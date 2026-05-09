# tester_duplicate.py

from __future__ import annotations

import sys
from typing import List

from textfsmgen.cli_old.tester.tester_paths import (
    resolve_case_path,
    generate_duplicate_case_name,
    resolve_case_creation_path,
)
from .tester_manifest_model import load_manifest, write_manifest
from .tester_files import (
    copy_main_authoritative_files,
    copy_non_main_authoritative_files,
)
from .tester_quicktest import run_quick_test_for_case


def handle_tester_duplicate(argv: List[str]) -> int:
    """
    textfsmgen tester duplicate author=<author> <target-case>
    """
    if len(argv) < 2:
        print("error: usage: tester duplicate author=<author> <target-case>", file=sys.stderr)
        return 1

    author_token, target_case = argv[0], argv[1]
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

    new_case = generate_duplicate_case_name(target_case)
    new_dir = resolve_case_creation_path(new_case, manifest.category)
    if new_dir is None:
        print("error: cannot determine creation path for duplicate case", file=sys.stderr)
        return 1

    if manifest.category == "main":
        copy_main_authoritative_files(src=target_dir, dst=new_dir)
    else:
        copy_non_main_authoritative_files(src=target_dir, dst=new_dir)

    write_manifest(new_dir, manifest)

    run_quick_test_for_case(new_dir)

    print(f"Duplicated case '{target_case}' to '{new_case}' with author='{author}'.")
    return 0
