from __future__ import annotations

from pathlib import Path
import json

from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors
from ..core.data_loader import extract_subpath_after
from textfsmgen.libs.common import parse_textfsm_to_dicts


@catch_path_errors
def merge_review(dst: Path, srcs: list[Path]) -> int:
    """
    Preview merge with dst as the reference case.
    Shows:
      - whether dst's template can parse all src inputs
      - detailed diagnostics for failures
      - input merge plan (copy, skip, rename)
      - expected artifacts that would be generated
    """

    print("[REVIEW] Merge review starting...\n")

    # --------------------------------------------------------------
    # Validate integration cases
    # --------------------------------------------------------------
    all_cases = [dst] + srcs
    for p in all_cases:
        case = GoldenCase.from_path(p)
        if not case.is_integration():
            print(f"[FAIL] Not an integration case: {p}")
            return 1

    # --------------------------------------------------------------
    # Validate builder_type consistency
    # --------------------------------------------------------------
    builder_types = set()
    for p in all_cases:
        manifest = json.loads((p / "manifest.json").read_text())
        builder_types.add(manifest.get("builder"))

    if len(builder_types) != 1:
        print(f"[FAIL] Cases have different builder_type values: {builder_types}")
        return 1

    builder_type = next(iter(builder_types))
    print(f"[REVIEW] builder = {builder_type}\n")

    # --------------------------------------------------------------
    # Load reference template from dst
    # --------------------------------------------------------------
    dst_case = GoldenCase.from_path(dst)
    dst_expected = dst_case.data.load_expected()
    template = dst_expected.template.content

    dst_case_name = extract_subpath_after("golden", dst_case.case_dir)

    print(f"[REVIEW] Reference case: {dst_case_name}\n")

    # --------------------------------------------------------------
    # Check if dst template can parse all src inputs
    # --------------------------------------------------------------
    print("[REVIEW] Checking template compatibility...\n")

    ok = True
    errors = []

    for src in srcs:
        src_case = GoldenCase.from_path(src)
        src_case_name = extract_subpath_after("golden", src_case.case_dir)
        for input_info in src_case.data.load_inputs():
            rows = parse_textfsm_to_dicts(template, input_info.content)
            if not rows:
                ok = False
                errors.append(
                    f"Template from '{dst_case_name}' failed to parse "
                    f"input '{input_info.fullname}' from case '{src_case_name}'."
                )

    if not ok:
        print("[FAIL] Reference template cannot parse all inputs.\n")
        print("\n".join(f"  - {e}" for e in errors))
        print("\n[REVIEW] Merge would fail.")
        return 1

    print("[OK] Reference template successfully parses all inputs.\n")

    # --------------------------------------------------------------
    # Input merge preview
    # --------------------------------------------------------------
    print("[REVIEW] Input merge plan:\n")

    simulated_inputs = {}  # name → content

    for src in srcs:
        src_case = GoldenCase.from_path(src)
        src_case_name = extract_subpath_after("golden", src_case.case_dir)
        for inp in src_case.data.load_inputs():
            name = Path(inp.fullname).name
            content = inp.content

            if name not in simulated_inputs:
                simulated_inputs[name] = content
                print(f"  COPY   {name}  (from {src_case_name})")
                continue

            # conflict
            if simulated_inputs[name] == content:
                print(f"  SKIP   {name}  (identical content)")
            else:
                # generate new name
                base = Path(name).stem
                ext = Path(name).suffix
                counter = 2

                while True:
                    new_name = f"{base}_{counter}{ext}"
                    if new_name not in simulated_inputs:
                        simulated_inputs[new_name] = content
                        print(
                            f"  RENAME {name} → {new_name}  "
                            f"(different content from {src_case_name})"
                        )
                        break
                    counter += 1

    print("\n[REVIEW] Total merged inputs:", len(simulated_inputs), "\n")

    # --------------------------------------------------------------
    # Expected artifacts preview
    # --------------------------------------------------------------
    print("[REVIEW] Expected artifacts to be generated:")
    print("  - expected/snippet.txt (copied from dst)")
    print("  - expected/textfsm.template (copied from dst)")
    print("  - expected_results/<input>_result.json for each merged input\n")

    print("[REVIEW] Merge would succeed.")
    return 0
