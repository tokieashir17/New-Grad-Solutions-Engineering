import hashlib
import json
from pathlib import Path


def stable_id(company: str, source: str, source_id: str) -> str:
    raw = f"{company}|{source}|{source_id}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_jobs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_jobs(path: Path, jobs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            sorted(jobs, key=lambda x: (x["category"], x["company"].lower(), x["title"].lower())),
            indent=2,
            ensure_ascii=False,
        ) + "\n"
    )
