#!/usr/bin/env python3
"""
Validate manifest.json and golden test folder structure.

Checks:
- missing files
- invalid JSON
- wrong paths
- mismatched input/expected pairs
- empty canonical files
"""

import json
import pathlib
import sys


ROOT = pathlib.Path("tests/golden")


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"Missing file: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {path}: {e}"


def validate_case(case_dir: pathlib.Path):
    errors = []
    manifest_path = case_dir / "manifest.json"

    # -------------------------
    # 1. Validate manifest.json
    # -------------------------
    manifest, err = load_json(manifest_path)
    if err:
        errors.append(err)
        return errors  # cannot continue without manifest

    # -------------------------
    # 2. Validate canonical files
    # -------------------------
    canonical = manifest.get("canonical", {})
    required_canonical = ["sample", "snippet", "template", "result"]

    for key in required_canonical:
        rel = canonical.get(key)
        if not rel:
            errors.append(f"Missing canonical entry '{key}' in manifest.json")
            continue

        path = case_dir / rel
        if not path.exists():
            errors.append(f"Canonical file missing: {path}")
            continue

        # Check empty file
        if path.stat().st_size == 0:
            errors.append(f"Canonical file is empty: {path}")

        # Validate JSON for expected_result.json
        if key == "result":
            _, err = load_json(path)
            if err:
                errors.append(err)

    # -------------------------
    # 3. Validate input/expected pairs
    # -------------------------
    inputs = manifest.get("inputs", [])
    if not isinstance(inputs, list):
        errors.append("manifest.json: 'inputs' must be a list")
        return errors

    for entry in inputs:
        name = entry.get("name")
        input_rel = entry.get("input")
        expected_rel = entry.get("expected")

        if not name or not input_rel or not expected_rel:
            errors.append(f"Invalid input entry: {entry}")
            continue

        input_path = case_dir / input_rel
        expected_path = case_dir / expected_rel

        # Check input file
        if not input_path.exists():
            errors.append(f"Missing input file: {input_path}")
        elif input_path.stat().st_size == 0:
            errors.append(f"Input file is empty: {input_path}")

        # Check expected file
        if not expected_path.exists():
            errors.append(f"Missing expected file: {expected_path}")
        else:
            _, err = load_json(expected_path)
            if err:
                errors.append(err)

    return errors


def main():
    # Validate all cases or a specific one
    if len(sys.argv) > 1:
        cases = [sys.argv[1]]
    else:
        cases = [p.name for p in ROOT.iterdir() if p.is_dir()]

    print("\nGolden Test Manifest Validator\n")

    for case in cases:
        case_dir = ROOT / case
        print(f"Checking case: {case}")

        if not case_dir.exists():
            print(f"  ERROR: Case directory does not exist: {case_dir}\n")
            continue

        errors = validate_case(case_dir)

        if errors:
            print("  ❌ FAIL")
            for e in errors:
                print(f"    - {e}")
        else:
            print("  ✅ PASS")

        print()

    print("Done.\n")


if __name__ == "__main__":
    main()
