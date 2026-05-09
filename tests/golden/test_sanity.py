import os

from textfsmgen.core.data_loader import GoldenCaseInfo


class FakeDataLoader:
    """
    Minimal stub to test:
    - regen_golden pytest option
    - GOLDEN_WRITE_META env var
    - GoldenCaseInfo wiring
    """

    def __init__(self, info: GoldenCaseInfo):
        self.info = info
        self.kind = info.kind
        self.test_case = info.name
        self.path = info.path

    def regenerate(self):
        # Simulate regeneration
        (self.path / "regen.txt").write_text(
            f"Regenerated for {self.kind}/{self.test_case}",
            encoding="utf-8"
        )

    def generate_meta(self):
        if not os.getenv("GOLDEN_WRITE_META"):
            return

        (self.path / "meta_generated.txt").write_text(
            f"Meta written for {self.kind}/{self.test_case}",
            encoding="utf-8"
        )


def test_regen_golden_flag(tmp_path, regen_golden):
    """
    If --regen-golden is passed, regenerate() should run.
    Otherwise, it should not.
    """

    # Arrange
    case_dir = tmp_path / "sample_case"
    case_dir.mkdir()
    info = GoldenCaseInfo("main", "sample_case", case_dir)
    loader = FakeDataLoader(info)

    # Act
    if regen_golden:
        loader.regenerate()

    # Assert
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
    loader = FakeDataLoader(info)

    # Ensure env var is cleared
    os.environ.pop("GOLDEN_WRITE_META", None)

    # No env var → should NOT write
    loader.generate_meta()
    assert not (case_dir / "meta_generated.txt").exists()

    # With env var → should write
    os.environ["GOLDEN_WRITE_META"] = "1"
    loader.generate_meta()
    os.environ.pop("GOLDEN_WRITE_META", None)

    assert (case_dir / "meta_generated.txt").exists()

