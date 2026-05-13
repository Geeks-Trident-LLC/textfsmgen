from __future__ import annotations

from pathlib import Path
import json

from textfsmgen.libs.common import parse_textfsm_to_dicts

from ..core.data_loader import extract_subpath_after
from ..core.golden_case import GoldenCase
from ..core.utils import catch_path_errors


@catch_path_errors
def merge_preview(srcs: list[Path], compact: bool = False, is_json: bool = False) -> int:
    display = not (is_json or compact)

    if display:
        print("[PREVIEW] Merge preview starting...\n")

    # 1. Load and validate cases
    cases = merge_preview_load_and_validate_cases(srcs, display=display)
    if cases is None:
        return 1

    # 2. Validate builder type
    builder_type = merge_preview_validate_builder_type(cases, display=display)
    if builder_type is None:
        return 1

    # JSON/compact do not print builder here
    if display:
        print(f"[PREVIEW] builder = {builder_type}\n")

    # 3. Evaluate reference candidates
    ref_case, candidate_info = merge_preview_select_reference_case(cases, display=display)

    if ref_case is None:
        if is_json:
            print(merge_preview_json_fail(builder_type, candidate_info))
        else:
            if display:
                print("[PREVIEW] No valid reference case found. Merge would fail.")
        return 1

    ref_case_name = extract_subpath_after("golden", ref_case.case_dir)

    if display:
        print(f"[PREVIEW] Reference case selected: {ref_case_name}\n")

    # 4. Simulate input merge
    merge_actions, simulated_inputs = merge_preview_simulate_input_merge(cases, ref_case)

    # 5. Output modes
    if is_json:
        print(merge_preview_json_success(
            builder_type,
            ref_case_name,
            candidate_info,
            merge_actions,
            simulated_inputs
        ))
        return 0

    if compact:
        merge_preview_print_compact(
            builder_type,
            ref_case_name,
            merge_actions,
            simulated_inputs
        )
        return 0

    # 6. Normal aligned printing
    merge_preview_print_merge_plan(merge_actions)
    print("\n[PREVIEW] Total merged inputs:", len(simulated_inputs), "\n")

    print("[PREVIEW] Expected artifacts to be generated:")
    print("  - expected/snippet.txt (from reference case)")
    print("  - expected/textfsm.template (from reference case)")
    print("  - expected_results/<input>_result.json for each merged input\n")

    print("[PREVIEW] Merge would succeed.")
    return 0



def merge_preview_load_and_validate_cases(srcs: list[Path], display=False):
    cases = []
    for p in srcs:
        if not p.exists():
            if display:
                print(f"[FAIL] Case does not exist: {p}")
            return None

        case = GoldenCase.from_path(p)
        if not case.is_integration():
            if display:
                print(f"[FAIL] Not an integration case: {p}")
            return None

        cases.append(case)

    return cases


def merge_preview_validate_builder_type(cases: list[GoldenCase], display=False):
    builder_types = set()

    for case in cases:
        manifest = case.data.load_manifest()
        builder_types.add(manifest.get("builder"))

    if len(builder_types) != 1:
        if display:
            print(f"[FAIL] Sources have different builder_type values: {builder_types}")
        return None

    return next(iter(builder_types))


def merge_preview_select_reference_case(cases: list[GoldenCase], display=False):
    if display:
        print("[PREVIEW] Evaluating reference candidates...\n")

    ref_candidates = []
    diagnostics = {}
    printed_lines = []

    for case_i in cases:
        template_i = case_i.data.load_expected().template.content
        case_i_name = extract_subpath_after("golden", case_i.case_dir)

        ok = True
        fail_messages = []

        for case_j in cases:
            all_inputs_passed = True

            for input_info, result_info in case_j.data.load_input_result_pairs():
                rows = parse_textfsm_to_dicts(template_i, input_info.content)
                exp_result = result_info.content

                if rows != exp_result or (rows == exp_result and not rows):
                    all_inputs_passed = False

            if not all_inputs_passed:
                ok = False
                case_j_name = extract_subpath_after("golden", case_j.case_dir)
                fail_messages.append(
                    f'Its template failed to parse all inputs from case "{case_j_name}".'
                )

        if ok:
            ref_candidates.append(case_i)
            diagnostics[case_i_name] = {"status": "ok", "errors": []}
            if display:
                printed_lines.append(f"[OK] Reference candidate: {case_i_name}")
        else:
            diagnostics[case_i_name] = {"status": "fail", "errors": fail_messages}

            if display:
                printed_lines.append(
                    f"[INFO] {case_i_name} cannot be a reference candidate:\n"
                    + "\n".join(f"    - {m}" for m in fail_messages)
                )

    if display:
        print("\n".join(printed_lines), "\n")

    return (ref_candidates[0] if ref_candidates else None), diagnostics


def merge_preview_simulate_input_merge(cases: list[GoldenCase], ref_case: GoldenCase):
    simulated_inputs = {}
    merge_actions = []

    ref_case_name = extract_subpath_after("golden", ref_case.case_dir)

    # BASE inputs
    for inp in ref_case.data.load_inputs():
        fullname = inp.fullname
        name = Path(inp.fullname).name
        simulated_inputs[fullname] = inp.content
        merge_actions.append(("BASE", name, "", ref_case_name))

    # Merge others
    for case in cases:
        if case is ref_case:
            continue

        case_name = extract_subpath_after("golden", case.case_dir)

        for inp in case.data.load_inputs():
            fullname = inp.fullname
            name = Path(inp.fullname).name
            content = inp.content

            if name not in simulated_inputs:
                simulated_inputs[fullname] = content
                merge_actions.append(("COPY", name, "", case_name))
                continue

            if simulated_inputs[fullname] == content:
                merge_actions.append(("OVERWRITE", name, "", case_name))
                continue

            # rename
            base = Path(name).stem
            dir_path = Path(name).parent
            ext = Path(name).suffix
            counter = 2

            while True:
                new_name = f"{base}_{counter}{ext}"
                new_fullname = str(dir_path / new_name)
                if new_name not in simulated_inputs:
                    simulated_inputs[new_fullname] = content
                    merge_actions.append(("RENAME", name, new_name, case_name))
                    break
                counter += 1

    return merge_actions, simulated_inputs


def merge_preview_print_merge_plan(merge_actions):
    # Compute widths
    action_w = max(len(a[0]) for a in merge_actions)
    name_w   = max(len(a[1]) for a in merge_actions)
    new_w    = max(len(a[2]) for a in merge_actions)

    for action, name, new_name, src in merge_actions:
        if action == "RENAME":
            print(f"  {action:<{action_w}}  {name:<{name_w}} → {new_name:<{new_w}}  (from {src})")
        else:
            print(f"  {action:<{action_w}}  {name:<{name_w}}      (from {src})")


def merge_preview_print_compact(builder, ref_case_name, merge_actions, simulated_inputs):
    base = sum(1 for a in merge_actions if a[0] == "BASE")
    copied = sum(1 for a in merge_actions if a[0] == "COPY")
    overwritten = sum(1 for a in merge_actions if a[0] == "OVERWRITE")
    renamed = sum(1 for a in merge_actions if a[0] == "RENAME")

    print(f"[PREVIEW] builder = {builder}")
    print(f"[PREVIEW] Reference case: {ref_case_name}")
    print(
        f"[PREVIEW] Inputs merged: {len(simulated_inputs)} "
        f"(base={base}, copied={copied}, overwritten={overwritten}, renamed={renamed})"
    )
    print("[PREVIEW] Expected artifacts: snippet, template, expected_results/*")
    print("[PREVIEW] Merge would succeed.")


def merge_preview_json_success(builder, ref_case_name, candidate_info, merge_actions, simulated_inputs):
    reference_candidates = {}
    for case, value in candidate_info.items():
        key = (
            str(extract_subpath_after("golden", case))
            if isinstance(case, Path) and case.is_absolute() else
            str(case)
        )
        reference_candidates[key] = value

    data = {
        "builder": builder,
        "reference_case": f"{ref_case_name}",
        "reference_candidates": reference_candidates,
        "inputs": {
            "total": len(simulated_inputs),
            "actions": [
                {
                    "action": f"{a}",
                    "name": f"{n}",
                    "new_name": f"{new}" if new else None,
                    "source": f"{src}"
                }
                for (a, n, new, src) in merge_actions
            ]
        },
        "expected_artifacts": [
            "expected/snippet.txt",
            "expected/textfsm.template",
            "expected_results/<input>_result.json"
        ],
        "result": "success"
    }
    return json.dumps(data, indent=2)


def merge_preview_json_fail(builder, candidate_info):
    reference_candidates = {}
    for case, value in candidate_info.items():
        key = (
            str(extract_subpath_after("golden", case))
            if isinstance(case, Path) and case.is_absolute() else
            str(case)
        )
        reference_candidates[key] = value

    data = {
        "builder": builder,
        "reference_case": None,
        "reference_candidates": reference_candidates,
        "result": "fail"
    }
    return json.dumps(data, indent=2)
