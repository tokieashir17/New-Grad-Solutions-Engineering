import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from src.experience import parse_experience, format_experience


def _experience_label(job: dict) -> str:
    """Display string for a job's experience requirement. Prefers a
    structured dict stored under job["experience"] (see experience.py);
    falls back to parsing the description directly for older job records
    that don't have it yet."""
    exp = job.get("experience")
    if isinstance(exp, dict):
        return format_experience(exp)
    return format_experience(parse_experience(f"{job.get('title', '')}. {job.get('description', '')}"))




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
                f"| {_cell(job['category'])} | {_experience_label(job)} "
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
                    f"| {_experience_label(job)} | {early} | [Apply]({job['url']}) |"
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