from collections import Counter
from datetime import date, timedelta
from pathlib import Path


def generate_readme(jobs: list[dict], path: Path) -> None:
    today = date.today()
    cutoff = today - timedelta(days=7)

    jobs = sorted(
        jobs,
        key=lambda j: (-j["score"], j["company"].lower(), j["title"].lower()),
    )

    counts = Counter(j["category"] for j in jobs)
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
        lines.append(f"- **{category}** — {counts[category]}")

    lines += ["", "## Recently Added", ""]

    if recent:
        lines += [
            "| Company | Role | Location | Category | Apply |",
            "|---|---|---|---|---|",
        ]
        for job in recent[:50]:
            lines.append(
                f"| {job['company']} | {job['title']} | {job['location'] or 'Not specified'} "
                f"| {job['category']} | [Apply]({job['url']}) |"
            )
    else:
        lines.append("_No jobs have been added in the last 7 days._")

    lines += ["", "## All Current Jobs", ""]

    if jobs:
        lines += [
            "| Company | Role | Location | Category | Early Career | Apply |",
            "|---|---|---|---|---|---|",
        ]
        for job in jobs:
            early = "Yes" if job["early_career"] else "Review"
            lines.append(
                f"| {job['company']} | {job['title']} | {job['location'] or 'Not specified'} "
                f"| {job['category']} | {early} | [Apply]({job['url']}) |"
            )
    else:
        lines.append(
            "_No jobs are loaded yet. Add real companies to `data/companies.json` and run `python main.py`._"
        )

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
