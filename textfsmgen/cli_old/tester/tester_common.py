from pathlib import Path
import json


def find_golden_root() -> Path:
    """
    Returns the root directory of all golden test cases.
    Example: tests/golden/
    """
    root = Path("tests") / "golden"
    if not root.exists():
        raise FileNotFoundError(f"Golden root not found: {root}")
    return root


def find_case_root(case_name: str) -> Path | None:
    """
    Locate the case directory by scanning all categories.
    Example: tests/golden/<category>/<case_name>
    """
    golden_root = find_golden_root()

    for category_dir in golden_root.iterdir():
        if not category_dir.is_dir():
            continue

        case_dir = category_dir / case_name
        if case_dir.exists() and case_dir.is_dir():
            return case_dir

    return None


def load_manifest(case_root: Path) -> dict:
    """
    Load manifest.json from a case directory.
    """
    manifest_path = case_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    return json.loads(manifest_path.read_text())
