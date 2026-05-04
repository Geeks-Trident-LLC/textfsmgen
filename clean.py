#!/usr/bin/env python
from __future__ import annotations

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


ROOT_DIRS = [
    ".tox",
    "htmlcov",
    "build",
    "dist",
]

ROOT_CACHES = [
    ".pytest_cache",
    ".ruff_cache",
]

ROOT_FILES = [
    ".coverage",
    "search.txt",
]

RECURSIVE_DIR_NAMES = [
    "__pycache__",
]

RECURSIVE_FILE_EXTS = [
    ".pyc",
]


def remove_path(path: Path, dry_run: bool = False) -> None:
    if not path.exists():
        return
    if dry_run:
        print(f"[DRY] {path}")
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def clean_root(dry_run: bool = False) -> None:
    for name in ROOT_DIRS:
        remove_path(ROOT / name, dry_run=dry_run)

    for name in ROOT_CACHES:
        remove_path(ROOT / name, dry_run=dry_run)

    for name in ROOT_FILES:
        remove_path(ROOT / name, dry_run=dry_run)

    for egg in ROOT.glob("*.egg-info"):
        remove_path(egg, dry_run=dry_run)

    for cov in ROOT.glob(".coverage.*"):
        remove_path(cov, dry_run=dry_run)


def clean_recursive(dry_run: bool = False) -> None:
    for dirpath, dirnames, filenames in os.walk(ROOT):
        path = Path(dirpath)

        # __pycache__ dirs
        for d in list(dirnames):
            if d in RECURSIVE_DIR_NAMES:
                remove_path(path / d, dry_run=dry_run)
                # optional: prevent descending into it
                try:
                    dirnames.remove(d)
                except ValueError:
                    pass

        # *.pyc files
        for fname in filenames:
            if Path(fname).suffix in RECURSIVE_FILE_EXTS:
                remove_path(path / fname, dry_run=dry_run)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Clean Python build and cache artifacts.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting anything.",
    )
    args = parser.parse_args()

    clean_root(dry_run=args.dry_run)
    clean_recursive(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
