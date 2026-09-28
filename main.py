from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import re
from html import unescape

from src.collectors import collect_company
from src.classifier import classify
from src.readme import generate_readme
from src.storage import load_jobs, save_jobs, stable_id

ROOT = Path(__file__).parent
COMPANIES_PATH = ROOT / "data" / "companies.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
README_PATH = ROOT / "README.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY","DC","PR","GU","VI","AS","MP"
}

US_STATE_NAMES = {
    "alabama","alaska","arizona","arkansas","california","colorado","connecticut","delaware",
    "florida","georgia","hawaii","idaho","illinois","indiana","iowa","kansas","kentucky",
    "louisiana","maine","maryland","massachusetts","michigan","minnesota","mississippi",
    "missouri","montana","nebraska","nevada","new hampshire","new jersey","new mexico",
    "new york","north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania",
    "rhode island","south carolina","south dakota","tennessee","texas","utah","vermont",
    "virginia","washington","west virginia","wisconsin","wyoming","district of columbia"
}

NON_US_MARKERS = (
    "canada", "united kingdom", "uk", "england", "ireland", "australia", "new zealand",
    "germany", "france", "spain", "netherlands", "singapore", "india", "japan", "brazil",
    "mexico", "switzerland", "israel", "poland", "portugal", "italy", "sweden", "denmark"
)

def is_us_location(location: str) -> bool:
    s = (location or "").strip().lower()
    if not s or s == "remote":
        return False
    if any(marker in s for marker in NON_US_MARKERS):
        return False
    if re.search(r"\b(?:united states|u\.?s\.?a?\b|usa)\b", s):
        return True
    if re.search(r"(?:^|[,/\- ])(?:" + "|".join(US_STATES) + r")(?:$|[,/\- ])", location.upper()):
        return True
    if any(name in s for name in US_STATE_NAMES):
        return True
    if re.search(r"\bremote\b.*\b(?:us|u\.?s\.?|usa|united states)\b", s):
        return True
    return False

def max_required_experience(description: str) -> bool:
    text = re.sub(r"<[^>]+>", " ", unescape(description or ""))
    text = re.sub(r"\s+", " ", text).lower()

    # Explicit experience requirements. 2+ years or less
    patterns = [
        r"\b(?:at least|minimum(?: of)?|requires?|required to have|must have|you have)\s+(\d+)\s*(?:\+|years?|yrs?)",
        r"\b(\d+)\s*\+\s*(?:years?|yrs?)\s*(?:of\s+)?(?:relevant\s+)?experience\b",
        r"\b(\d+)\s*(?:-|–)\s*(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:relevant\s+)?experience\b",
        r"\b(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:relevant\s+)?experience\b",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            nums = [int(x) for x in m.groups() if x is not None and x.isdigit()]
            if nums and max(nums) > 2:
                return False
    return True

def main() -> None:
    companies = json.loads(COMPANIES_PATH.read_text())
    # Rebuild the dataset each run so jobs that no longer satisfy the filters cannot linger.
    existing = []
    existing_by_id = {}

    today = datetime.now(timezone.utc).date().isoformat()
    collected = 0
    accepted = 0
    filtered_location = 0
    filtered_experience = 0

    for company in companies:
        try:
            raw_jobs = collect_company(company)
        except Exception as exc:
            logging.warning("Failed to collect %s: %s", company["name"], exc)
            continue
        logging.info("Collected %d postings from %s", len(raw_jobs), company["name"])
        collected += len(raw_jobs)

        for raw in raw_jobs:
            if not is_us_location(raw["location"]):
                filtered_location += 1
                continue
            if not max_required_experience(raw["description"]):
                filtered_experience += 1
                continue

            result = classify(raw["title"], raw["description"], raw["location"])
            if not result["relevant"]:
                continue

            job_id = stable_id(raw["company"], raw["source"], raw["source_id"])
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
    logging.info("Collected: %d | Matching: %d | Stored: %d | Non-US filtered: %d | >2 years filtered: %d", collected, accepted, len(jobs), filtered_location, filtered_experience)

if __name__ == "__main__":
    main()
