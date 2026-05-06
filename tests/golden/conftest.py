import pathlib
import pytest

from tests.golden.golden_test_utils import (
    load_manifest,
    load_canonical_from_manifest,
    load_inputs_from_manifest,
    get_builder_type,
    sync_datetime,
)

gold_path = pathlib.Path(__file__).parent


# ============================================================
# Parametrize golden test cases
# ============================================================
def pytest_generate_tests(metafunc):
    if "case" not in metafunc.fixturenames:
        return

    cases = [
        p.name
        for p in gold_path.iterdir()
        if p.is_dir() and (p / "manifest.json").exists()
    ]

    metafunc.parametrize("case", sorted(cases))


# ============================================================
# Golden fixtures
# ============================================================
@pytest.fixture
def golden(request):
    if request.config.is_golden_enabled:
        return request.getfixturevalue("golden_enabled")

    # Golden disabled → return dummy
    return {"case": None}


@pytest.fixture
def golden_enabled(case, request):
    case_dir = gold_path / case
    manifest = load_manifest(case_dir)
    canonical = load_canonical_from_manifest(case_dir, manifest)
    inputs = load_inputs_from_manifest(case_dir, manifest)
    Builder = get_builder_type(manifest)

    if request.config.getoption("--debug-golden"):
        print(f"\n[golden-debug] Case: {case}")
        print(f"  Path: {case_dir}")
        print(f"  Manifest keys: {list(manifest.keys())}")
        print(f"  Canonical files: {manifest['canonical']}")
        print(f"  Inputs: {[i[0] for i in inputs]}")
        print(f"  Builder: {Builder.__name__}\n")

    return {
        "case": case,
        "manifest": manifest,
        "canonical": canonical,
        "inputs": inputs,
        "Builder": Builder,
        "sync_datetime": sync_datetime,
    }
