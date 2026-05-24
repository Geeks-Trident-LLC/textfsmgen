import os
from textfsmgen.core.case_loader import GoldenCaseInfo


class FakeCase:
    """
    Minimal stub to test:
    - pytest --regen-golden flag behavior
    - GOLDEN_WRITE_META env var
    - GoldenCaseInfo wiring
    """

    def __init__(self, info: GoldenCaseInfo):
        self.info = info
        self.kind = info.kind
        self.name = info.name
        self.path = info.path

    def regenerate(self):
        # Simulate regeneration
        (self.path / "regen.txt").write_text(
            f"Regenerated for {self.kind}/{self.name}", encoding="utf-8"
        )

    def generate_meta(self):
        # Only write meta when explicitly allowed
        if not os.getenv("GOLDEN_WRITE_META"):
            return

        (self.path / "meta_generated.txt").write_text(
            f"Meta written for {self.kind}/{self.name}", encoding="utf-8"
        )


def test_regen_golden_flag(tmp_path, regen_golden):
    """
    If --regen-golden is passed, regenerate() should run.
    Otherwise, it should not.
    """

    case_dir = tmp_path / "sample_case"
    case_dir.mkdir()

    info = GoldenCaseInfo("main", "sample_case", case_dir)
    case = FakeCase(info)

    if regen_golden:
        case.regenerate()

    regen_file = case_dir / "regen.txt"

    if regen_golden:
        assert regen_file.exists()
    else:
        assert not regen_file.exists()


def test_generate_meta_env_var(tmp_path):
    """
    generate_meta() should only write when GOLDEN_WRITE_META=1
    """

    case_dir = tmp_path / "sample_case"
    case_dir.mkdir()

    info = GoldenCaseInfo("integration", "sample_case", case_dir)
    case = FakeCase(info)

    # Ensure env var is cleared
    os.environ.pop("GOLDEN_WRITE_META", None)

    # No env var → should NOT write
    case.generate_meta()
    assert not (case_dir / "meta_generated.txt").exists()

    # With env var → should write
    os.environ["GOLDEN_WRITE_META"] = "1"
    case.generate_meta()
    os.environ.pop("GOLDEN_WRITE_META", None)

    assert (case_dir / "meta_generated.txt").exists()

