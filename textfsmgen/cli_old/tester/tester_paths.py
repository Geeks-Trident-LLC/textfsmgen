# tester_paths.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .tester_common import find_case_root, load_manifest

# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def resolve_case_creation_path(case: str, category: str) -> Optional[Path]:
    """
    Resolve where a NEW case should be created, using the unified path
    resolution rules documented in the CLI Tester Guide.

    Returns:
        Path to the new case directory, or None if no rule matches.
    """
    pwd = Path.cwd()

    # Rule 5: <case> is a full path
    if _is_full_path(case):
        full = Path(case).resolve()
        return full if _is_valid_full_path(full, category) else None

    # Rule 1: pwd ends with tests/golden/<category>
    if _ends_with_category_dir(pwd, category):
        return pwd / case

    # Rule 2: pwd ends with tests/golden
    if _ends_with_golden_dir(pwd) and _category_exists_in(pwd, category):
        return pwd / category / case

    # Rule 3: pwd ends with tests
    if _ends_with_tests_dir(pwd) and _category_exists_in(pwd / "golden", category):
        return pwd / "golden" / category / case

    # Rule 4: somewhere under project tree
    found = _find_category_dir_upwards(pwd, category)
    if found:
        return found / case

    # Rule 6: no match
    return None


def resolve_case_path(path: str) -> Path:
    """
    Resolve a test case path exactly as provided:
        tests/golden/<category>/<case>

    Rules:
    - If 'path' is absolute → use it directly.
    - If 'path' is relative → resolve relative to current working directory.
    - No guessing, no inference, no fallback.
    """

    raw = Path(path)

    # 1. Full path → use as-is
    if raw.is_absolute():
        folder = raw
    else:
        # 2. Relative path → join with current working directory
        folder = Path.cwd() / raw

    # Normalize
    folder = folder.resolve()

    # 3. Must exist and be a directory
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"case not found: {path}")

    # 4. Canonical-style case
    canonical_dir = folder / "canonical"
    if canonical_dir.exists():
        required = [
            folder / "manifest.json",
            canonical_dir / "sample.txt",
            canonical_dir / "snippet.txt",
            canonical_dir / "textfsm.template",
            canonical_dir / "result.json",
            folder / "inputs",
            folder / "expected_results",
        ]
        missing = [str(p.relative_to(folder)) for p in required if not p.exists()]
        if missing:
            raise ValueError(
                f"invalid test case: {path}; missing required files: {', '.join(missing)}"
            )
        return folder

    # 5. Expected-style case
    expected_dir = folder / "expected"
    if expected_dir.exists():
        required = [
            folder / "manifest.json",
            expected_dir / "snippet.txt",
            expected_dir / "textfsm.template",
            folder / "inputs",
            folder / "expected_results",
        ]
        missing = [str(p.relative_to(folder)) for p in required if not p.exists()]
        if missing:
            raise ValueError(
                f"invalid test case: {path}; missing required files: {', '.join(missing)}"
            )
        return folder

    # 6. Neither canonical/ nor expected/ exists → invalid
    raise ValueError(
        f"invalid test case: {path}; expected either 'canonical/' or 'expected/' folder"
    )



def generate_duplicate_case_name(case: str) -> str:
    """
    Generate <case>-duplicated, <case>-duplicated-2, <case>-duplicated-3, ...
    """
    base = f"{case}-duplicated"
    pwd = Path.cwd()    # noqa

    # First try <case>-duplicated
    if not _case_exists_anywhere(base):
        return base

    # Then try numbered suffixes
    n = 2
    while True:
        name = f"{base}-{n}"
        if not _case_exists_anywhere(name):
            return name
        n += 1


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _is_full_path(case: str) -> bool:
    return "/" in case or "\\" in case


def _is_valid_full_path(path: Path, category: str) -> bool:
    """
    Full path must contain .../tests/golden/<category>/...
    """
    parts = list(path.resolve().parts)
    try:
        idx = parts.index("golden")
    except ValueError:
        return False

    # Expect: .../tests/golden/<category>/...
    if idx == 0:
        return False
    if parts[idx - 1] != "tests":
        return False
    if idx + 1 >= len(parts):
        return False
    return parts[idx + 1] == category


def _ends_with_category_dir(pwd: Path, category: str) -> bool:
    """
    Check if pwd ends with tests/golden/<category>.
    """
    parts = pwd.parts
    if len(parts) < 3:
        return False
    return parts[-3:] == ("tests", "golden", category)


def _ends_with_golden_dir(pwd: Path) -> bool:
    """
    Check if pwd ends with tests/golden.
    """
    parts = pwd.parts
    if len(parts) < 2:
        return False
    return parts[-2:] == ("tests", "golden")


def _ends_with_tests_dir(pwd: Path) -> bool:
    """
    Check if pwd ends with tests.
    """
    return pwd.name == "tests"


def _category_exists_in(parent: Path, category: str) -> bool:
    """
    Check if parent/<category> exists.
    """
    return (parent / category).is_dir()


def _find_category_dir_upwards(start: Path, category: str) -> Optional[Path]:
    """
    Search upward for tests/golden/<category>.
    """
    for root in _walk_upwards(start):
        candidate = root / "tests" / "golden" / category
        if candidate.is_dir():
            return candidate
    return None


def _walk_upwards(start: Path):
    """
    Yield start, parent, parent-of-parent, ... until filesystem root.
    """
    current = start.resolve()
    while True:
        yield current
        if current.parent == current:
            break
        current = current.parent


def _case_exists_anywhere(case: str) -> bool:
    """
    Check if <case> exists anywhere under tests/golden/*.
    """
    pwd = Path.cwd()
    for root in _walk_upwards(pwd):
        golden = root / "tests" / "golden"
        if not golden.is_dir():
            continue

        for category_dir in golden.iterdir():
            if not category_dir.is_dir():
                continue
            if (category_dir / case).is_dir():
                return True

    return False


def handle_tester_paths(argv):
    if not argv:
        print("error: missing case name")
        return 1

    case = argv[0]
    case_root = find_case_root(case)
    if not case_root:
        print(f"error: case not found: {case}")
        return 1

    manifest = load_manifest(case_root)

    print(f"Case: {case}")
    print(f"Category: {case_root.parent.name}")
    print()
    print("Paths:")

    def show(label, path: Path):
        if path.exists():
            print(f"  {label:<22} {path}")
        else:
            print(f"  {label:<22} (not present)")

    # Always present
    show("manifest:", case_root / "manifest.json")
    show("meta:", case_root / "meta.json")

    # MAIN CASES
    canonical_dir = case_root / "canonical"
    if canonical_dir.exists():
        show("canonical dir:", canonical_dir)
        show("canonical snippet:", canonical_dir / "snippet.txt")
        show("canonical template:", canonical_dir / "textfsm.template")
        show("canonical sample:", canonical_dir / "sample.txt")
        show("canonical result:", canonical_dir / "result.json")

    # INTEGRATION CASES
    expected_dir = case_root / "expected"
    if expected_dir.exists():
        show("expected dir:", expected_dir)
        show("expected snippet:", expected_dir / "snippet.txt")
        show("expected template:", expected_dir / "textfsm.template")

    # Shared
    show("inputs dir:", case_root / "inputs")
    show("expected_results dir:", case_root / "expected_results")

    return 0

