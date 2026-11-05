"""Run locally: python find_slugs.py
Tries a few slug variants per company against Ashby, Workable, Recruitee,
and SmartRecruiters, and prints any that respond with real postings.
Workday isn't included here since its slug (tenant:wdN:site) can't be
guessed from a company name -- get that one from the careers page URL.
"""
import re
import time
import requests

HEADERS = {"User-Agent": "job-board-slug-finder/1.0"}

CANDIDATES = [
  "Stripe"
]


def variants(name: str) -> list[str]:
    base = re.sub(r"[^a-z0-9 ]", "", name.lower())
    out = {base.replace(" ", ""), base.replace(" ", "-")}
    # Preserve a capitalized form too, since Ashby slugs are case-sensitive
    out.add("".join(w.capitalize() for w in base.split()))
    return list(out)


def try_ashby(slug: str) -> int | None:
    r = requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}", timeout=10)
    if r.ok:
        return len(r.json().get("jobs", []))
    return None


def try_workable(slug: str) -> int | None:
    r = requests.get(
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
        params={"details": "true"}, timeout=10,
    )
    if r.ok:
        return len(r.json().get("jobs", []))
    return None


def try_recruitee(slug: str) -> int | None:
    r = requests.get(f"https://{slug}.recruitee.com/api/offers/", timeout=10)
    if r.ok:
        return len(r.json().get("offers", []))
    return None


def try_smartrecruiters(slug: str) -> int | None:
    r = requests.get(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
        params={"limit": 1}, timeout=10,
    )
    if r.ok:
        return r.json().get("totalFound", 0)
    return None


CHECKS = {
    "ashby": try_ashby,
    "workable": try_workable,
    "recruitee": try_recruitee,
    "smartrecruiters": try_smartrecruiters,
}


def main() -> None:
    found = []
    for name in CANDIDATES:
        for slug in variants(name):
            for ats, check in CHECKS.items():
                try:
                    count = check(slug)
                except requests.RequestException:
                    count = None
                if count:  # skip 0-posting boards, they're not worth adding
                    found.append({"name": name, "ats": ats, "slug": slug, "postings": count})
                    print(f"{name:20s} -> ats={ats:16s} slug={slug:20s} postings={count}")
                time.sleep(0.1)  # be polite to these public APIs

    print(f"\nFound {len(found)} working boards. Copy the ones you want into companies.json:")
    for f in found:
        print({"name": f["name"], "ats": f["ats"], "slug": f["slug"]})


if __name__ == "__main__":
    main()
