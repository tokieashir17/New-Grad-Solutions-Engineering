from datetime import datetime, timezone
import requests


HEADERS = {
    "User-Agent": "new-grad-solutions-engineering-job-board/1.0"
}


def _get_json(url: str, params: dict | None = None) -> dict | list:
    response = requests.get(url, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def _post_json(url: str, payload: dict) -> dict | list:
    response = requests.post(url, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def _join(*parts: str | None, sep: str = ", ") -> str:
    return sep.join(p for p in parts if p)


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


def lever(company: str, slug: str, host: str = "api.lever.co", source: str = "lever") -> list[dict]:
    url = f"https://{host}/v0/postings/{slug}"
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
            "source": source,
        })

    return jobs




def ashby(company: str, slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    data = _get_json(url, {"includeCompensation": "true"})
    jobs = []

    for job in data.get("jobs", []):
        if job.get("isListed") is False:
            continue

        secondary = [
            s.get("location", "") if isinstance(s, dict) else str(s)
            for s in (job.get("secondaryLocations") or [])
        ]
        location = _join(job.get("location"), *secondary, sep="; ")
        if job.get("isRemote") and "remote" not in location.lower():
            location = _join(location, "Remote", sep="; ")

        jobs.append({
            "source_id": str(job["id"]),
            "company": company,
            "title": job.get("title", ""),
            "location": location,
            "description": job.get("descriptionPlain") or job.get("descriptionHtml") or "",
            "url": job.get("jobUrl", ""),
            "source": "ashby",
        })

    return jobs


def smartrecruiters(company: str, slug: str, fetch_details: bool = False) -> list[dict]:
    """List endpoint has no description. Set fetch_details to pull one extra
    request per posting, which is slow on big boards."""
    base = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    jobs = []
    offset = 0

    while True:
        data = _get_json(base, {"limit": 100, "offset": offset})
        content = data.get("content", [])
        if not content:
            break

        for job in content:
            loc = job.get("location") or {}
            location = _join(loc.get("city"), loc.get("region"), (loc.get("country") or "").upper())
            if loc.get("remote"):
                location = _join(location, "Remote", sep=" | ")

            description = ""
            if fetch_details:
                detail = _get_json(f"{base}/{job['id']}")
                sections = (detail.get("jobAd") or {}).get("sections") or {}
                description = "\n\n".join(
                    s.get("text", "") for s in sections.values() if isinstance(s, dict)
                )

            jobs.append({
                "source_id": str(job["id"]),
                "company": company,
                "title": job.get("name", ""),
                "location": location,
                "description": description,
                "url": f"https://jobs.smartrecruiters.com/{slug}/{job['id']}",
                "source": "smartrecruiters",
            })

        offset += len(content)
        if offset >= data.get("totalFound", 0):
            break

    return jobs


def workable(company: str, slug: str) -> list[dict]:
    url = f"https://apply.workable.com/api/v1/widget/accounts/{slug}"
    data = _get_json(url, {"details": "true"})
    jobs = []

    for job in data.get("jobs", []):
        jobs.append({
            "source_id": str(job.get("shortcode") or job.get("id")),
            "company": company,
            "title": job.get("title", ""),
            "location": _join(job.get("city"), job.get("state"), job.get("country")),
            "description": job.get("description", "") or "",
            "url": job.get("url") or job.get("shortlink", ""),
            "source": "workable",
        })

    return jobs


def recruitee(company: str, slug: str) -> list[dict]:
    url = f"https://{slug}.recruitee.com/api/offers/"
    data = _get_json(url)
    jobs = []

    for job in data.get("offers", []):
        location = job.get("location") or _join(job.get("city"), job.get("country"))
        jobs.append({
            "source_id": str(job["id"]),
            "company": company,
            "title": job.get("title", ""),
            "location": location,
            "description": _join(job.get("description"), job.get("requirements"), sep="\n\n"),
            "url": job.get("careers_url", ""),
            "source": "recruitee",
        })

    return jobs


def workday(company: str, slug: str, fetch_details: bool = False) -> list[dict]:
    """slug format is 'tenant:wdN:site', for example 'nvidia:wd5:NVIDIAExternalCareerSite'.
    Take it from the careers URL: https://<tenant>.<wdN>.myworkdayjobs.com/<site>"""
    try:
        tenant, wd, site = slug.split(":")
    except ValueError:
        raise ValueError(f"Workday slug must look like 'tenant:wdN:site', got '{slug}'")

    host = f"https://{tenant}.{wd}.myworkdayjobs.com"
    list_url = f"{host}/wday/cxs/{tenant}/{site}/jobs"
    jobs = []
    offset = 0

    while True:
        data = _post_json(list_url, {
            "appliedFacets": {},
            "limit": 20,
            "offset": offset,
            "searchText": "",
        })
        postings = data.get("jobPostings", [])
        if not postings:
            break

        for job in postings:
            path = job.get("externalPath", "")

            description = ""
            if fetch_details and path:
                detail = _get_json(f"{host}/wday/cxs/{tenant}/{site}{path}")
                description = (detail.get("jobPostingInfo") or {}).get("jobDescription", "") or ""

            jobs.append({
                "source_id": path,
                "company": company,
                "title": job.get("title", ""),
                "location": job.get("locationsText", ""),
                "description": description,
                "url": f"{host}/{site}{path}",
                "source": "workday",
            })

        offset += len(postings)
        if offset >= data.get("total", 0):
            break

    return jobs


COLLECTORS = {
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
    "workable": workable,
    "recruitee": recruitee,
    "workday": workday,
}

# These accept an optional "fetch_details": true in companies.json
DETAIL_ATS = {"smartrecruiters", "workday"}


def collect_company(company: dict) -> list[dict]:
    ats = company["ats"].lower()
    collector = COLLECTORS.get(ats)
    if collector is None:
        raise ValueError(f"Unsupported ATS: {ats}")

    if ats in DETAIL_ATS:
        return collector(
            company["name"],
            company["slug"],
            fetch_details=company.get("fetch_details", False),
        )
    return collector(company["name"], company["slug"])


def utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()
