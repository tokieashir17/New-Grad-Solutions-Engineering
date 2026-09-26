from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Job:
    id: str
    company: str
    title: str
    category: str
    location: str
    remote: bool
    early_career: bool
    score: int
    signals: list[str]
    url: str
    source: str
    first_seen: str
    last_seen: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
