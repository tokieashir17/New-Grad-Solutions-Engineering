from datetime import datetime, timezone
import requests


HEADERS = {
    "User-Agent": "new-grad-solutions-engineering-job-board/1.0"
}


def _get_json(url: str, params: dict | None = None) -> dict | list:
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def greenhouse(company: str, slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    data = _get_json(url, {"content": "true"})
    jobs = []

    for job in data.get("jobs", []):
        jobs.append({
            "source_id": str(job["id"]),
            "company": company,
            "title": job.get("title", ""),
            "location": (job.get("location") or {}).get("name", ""),
            "description": job.get("content", "") or "",
            "url": job.get("absolute_url", ""),
            "source": "greenhouse",
        })

    return jobs


def lever(company: str, slug: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}"
    data = _get_json(url, {"mode": "json"})
    jobs = []

    for job in data:
        categories = job.get("categories") or {}
        locations = categories.get("allLocations") or []
        location = categories.get("location") or ", ".join(locations)

        jobs.append({
            "source_id": str(job["id"]),
            "company": company,
            "title": job.get("text", ""),
            "location": location,
            "description": job.get("descriptionPlain", "") or "",
            "url": job.get("hostedUrl", ""),
            "source": "lever",
        })

    return jobs


def collect_company(company: dict) -> list[dict]:
    ats = company["ats"].lower()
    if ats == "greenhouse":
        return greenhouse(company["name"], company["slug"])
    if ats == "lever":
        return lever(company["name"], company["slug"])
    raise ValueError(f"Unsupported ATS: {ats}")


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()
