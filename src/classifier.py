import re

ROLE_RULES = {
    "Solutions Engineering": [
        r"\bsolutions engineer\b",
        r"\bsolutions consultant\b",
        r"\btechnical solutions\b",
    ],
    "Sales Engineering": [
        r"\bsales engineer\b",
        r"\bpre[- ]sales\b",
        r"\bpre[- ]sales engineer\b",
        r"\btechnical sales\b",
    ],
    "Forward Deployed Engineering": [
        r"\bforward[- ]deployed\b",
        r"\bforward deployed engineer\b",
        r"\bfield engineer\b",
        r"\bcustomer engineer\b",
    ],
    "Implementation Engineering": [
        r"\bimplementation engineer\b",
        r"\bimplementation consultant\b",
        r"\bdeployment engineer\b",
    ],
    "Technical Consulting": [
        r"\btechnical consultant\b",
        r"\btechnical consulting\b",
        r"\bsolutions architect\b",
    ],
}

EARLY_RULES = [
    ("new grad", r"\bnew[- ]grad(?:uate)?\b"),
    ("entry level", r"\bentry[- ]level\b"),
    ("early career", r"\bearly[- ]career\b"),
    ("associate", r"\bassociate\b"),
    ("junior", r"\bjunior\b"),
    ("0-1 years", r"\b0\s*[-–]\s*1\s+years?\b"),
    ("0-2 years", r"\b0\s*[-–]\s*2\s+years?\b"),
    ("1-2 years", r"\b1\s*[-–]\s*2\s+years?\b"),
    ("1+ years", r"\b1\+?\s+years?\b"),
]

SENIOR_RULES = [
    r"\bsenior\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\blead\b",
    r"\bmanager\b",
    r"\bdirector\b",
    r"\bvice president\b",
    r"\bvp\b",
]

REMOTE_RULES = [
    r"\bremote\b",
    r"\bwork from home\b",
    r"\bremote[- ]first\b",
]

US_RULES = [
    r"\bunited states\b",
    r"\busa\b",
    r"\bnew york\b",
    r"\bboston\b",
    r"\bsan francisco\b",
    r"\bseattle\b",
    r"\bchicago\b",
    r"\baustin\b",
    r"\bdenver\b",
    r"\bwashington,?\s*d\.?c\.?\b",
]


def _matches(text: str, rules: list[str]) -> list[str]:
    return [rule for rule in rules if re.search(rule, text, re.I)]


def classify(title: str, description: str, location: str) -> dict:
    text = f"{title}\n{description}".lower()

    categories = []
    for category, rules in ROLE_RULES.items():
        if _matches(text, rules):
            categories.append(category)

    senior_hits = _matches(text, SENIOR_RULES)
    early_hits = []
    for label, rule in EARLY_RULES:
        if re.search(rule, text, re.I):
            early_hits.append(label)

    remote = bool(_matches(text, REMOTE_RULES)) or "remote" in location.lower()

    score = 0
    if categories:
        score += 10
    score += min(len(early_hits) * 4, 12)
    if remote:
        score += 2
    if re.search(r"\bbachelor'?s\b|\bcomputer science\b|\bengineering degree\b", text, re.I):
        score += 1
    if senior_hits:
        score -= 20

    # Strong title-level exclusion.
    title_senior = bool(_matches(title.lower(), SENIOR_RULES))

    early_career = bool(early_hits) and not title_senior and not senior_hits
    relevant = bool(categories) and not title_senior and not senior_hits

    if not relevant:
        return {
            "relevant": False,
            "category": "",
            "early_career": False,
            "remote": remote,
            "score": score,
            "signals": [],
        }

    # Prefer the first matching category, but preserve multi-category evidence.
    category = categories[0]
    signals = categories + early_hits
    return {
        "relevant": True,
        "category": category,
        "early_career": early_career,
        "remote": remote,
        "score": score,
        "signals": signals,
    }
