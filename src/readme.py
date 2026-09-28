import html
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path


_TAG_RE = re.compile(r"<[^>]+>")
_YEARS_RE = re.compile(
    r"(\d{1,2})\s*(\+|(?:-|–|to)\s*(\d{1,2}))?\s*(?:or more\s*)?(?:years?|yrs?)\b",
    re.I,
)


def _clean_text(text: str) -> str:
    # Greenhouse returns HTML-escaped HTML, so unescape, strip tags, unescape again
    text = html.unescape(text or "")
    text = _TAG_RE.sub(" ", text)
    return html.unescape(text)


def extract_years(job: dict) -> str:
    """minimum years of experience listed."""
    if job.get("experience"):
        return job["experience"]

    text = _clean_text(f"{job.get('title', '')}. {job.get('description', '')}")
    found = []

    for m in _YEARS_RE.finditer(text):
        window = text[max(0, m.start() - 60): m.end() + 60].lower()
        if "experience" not in window:
            continue

        low = int(m.group(1))
        high = int(m.group(3)) if m.group(3) else None
        before = text[max(0, m.start() - 20): m.start()].lower()
        plus = (
            m.group(2) == "+"
            or "or more" in m.group(0).lower()
            or "at least" in before
            or "minimum" in before
        )
        found.append((low, high, plus))

    if not found:
        return "Not stated"

    # prefers the lowest listed number
    low, high, plus = min(found, key=lambda f: f[0])
    if high:
        return f"{low}-{high} yrs"
    return f"{low}+ yrs" if plus else f"{low} yrs"


def _cell(value) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _anchor(text: str) -> str:
    return re.sub(r"[^\w\- ]", "", text.lower()).strip().replace(" ", "-")


def generate_readme(jobs: list[dict], path: Path) -> None:
    today = date.today()
    cutoff = today - timedelta(days=7)

    jobs = sorted(
        jobs,
        key=lambda j: (-j["score"], j["company"].lower(), j["title"].lower()),
    )

    counts = Counter(j["category"] for j in jobs)
    by_category = defaultdict(list)
    for job in jobs:
        by_category[job["category"]].append(job)

    recent = [j for j in jobs if j.get("first_seen", "") >= cutoff.isoformat()]

    lines = [
        "# New Grad Solutions Engineering Jobs",
        "",
        "> Automatically updated job listings for early-career Solutions Engineering, Sales Engineering, Forward Deployed Engineering, Customer Engineering, and related roles.",
        "",
        f"**Last updated:** {today.isoformat()}  ",
        f"**Matching jobs:** {len(jobs)}",
        "",
        "## Categories",
        "",
    ]

    for category in sorted(counts):
        lines.append(f"- [{category}](#{_anchor(category)}) ({counts[category]})")

    lines += ["", "## Recently Added", ""]

    if recent:
        lines += [
            "| Company | Role | Location | Category | Experience | Apply |",
            "|---|---|---|---|---|---|",
        ]
        for job in recent[:50]:
            lines.append(
                f"| {_cell(job['company'])} | {_cell(job['title'])} "
                f"| {_cell(job['location']) or 'Not specified'} "
                f"| {_cell(job['category'])} | {extract_years(job)} "
                f"| [Apply]({job['url']}) |"
            )
    else:
        lines.append("_No jobs have been added in the last 7 days._")

    if jobs:
        for category in sorted(by_category):
            lines += [
                "",
                f"## {category}",
                "",
                "| Company | Role | Location | Experience | Early Career | Apply |",
                "|---|---|---|---|---|---|",
            ]
            for job in by_category[category]:
                early = "Yes" if job["early_career"] else "Review"
                lines.append(
                    f"| {_cell(job['company'])} | {_cell(job['title'])} "
                    f"| {_cell(job['location']) or 'Not specified'} "
                    f"| {extract_years(job)} | {early} | [Apply]({job['url']}) |"
                )
    else:
        lines += [
            "",
            "## All Current Jobs",
            "",
            "_No jobs are loaded yet. Add real companies to `data/companies.json` and run `python main.py`._",
        ]

    lines += [
        "",
        "---",
        "",
        "## About",
        "",
        "This repository collects publicly published job postings from supported ATS platforms.",
        "Always verify the role and requirements on the employer's application page.",
        "",
    ]

    path.write_text("\n".join(lines) + "\n")
