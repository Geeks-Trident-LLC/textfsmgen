from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GoldenCaseInfo:
    kind: str
    name: str
    path: Path
