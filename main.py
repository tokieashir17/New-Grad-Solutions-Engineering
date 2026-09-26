from datetime import datetime, timezone
from pathlib import Path
import json
import logging

from src.collectors import collect_company
from src.classifier import classify
from src.readme import generate_readme
from src.storage import load_jobs, save_jobs, stable_id


ROOT = Path(__file__).parent
COMPANIES_PATH = ROOT / "data" / "companies.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
README_PATH = ROOT / "README.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    companies = json.loads(COMPANIES_PATH.read_text())
    existing = load_jobs(JOBS_PATH)
    existing_by_id = {job["id"]: job for job in existing}

    today = datetime.now(timezone.utc).date().isoformat()
    collected = 0
    accepted = 0

    for company in companies:
        try:
            raw_jobs = collect_company(company)
        except Exception as exc:
            logging.warning("Failed to collect %s: %s", company["name"], exc)
            continue

        logging.info("Collected %d postings from %s", len(raw_jobs), company["name"])
        collected += len(raw_jobs)

        for raw in raw_jobs:
            result = classify(
                raw["title"],
                raw["description"],
                raw["location"],
            )

            if not result["relevant"]:
                continue

            job_id = stable_id(
                raw["company"],
                raw["source"],
                raw["source_id"],
            )

            old = existing_by_id.get(job_id)
            existing_by_id[job_id] = {
                "id": job_id,
                "company": raw["company"],
                "title": raw["title"].strip(),
                "category": result["category"],
                "location": raw["location"].strip(),
                "remote": result["remote"],
                "early_career": result["early_career"],
                "score": result["score"],
                "signals": result["signals"],
                "url": raw["url"],
                "source": raw["source"],
                "first_seen": old["first_seen"] if old else today,
                "last_seen": today,
            }
            accepted += 1

    jobs = list(existing_by_id.values())
    save_jobs(JOBS_PATH, jobs)
    generate_readme(jobs, README_PATH)

    logging.info("Collected: %d | Matching: %d | Stored: %d", collected, accepted, len(jobs))


if __name__ == "__main__":
    main()
