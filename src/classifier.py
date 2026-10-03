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
        r"\bdeployment strategist\b",
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
    "GTM Engineering": [
        r"\bgtm engineers?\b",
        r"\bgo[- ]to[- ]market engineers?\b",
        r"\btechnical gtm\b",
    ],
    "Sales Development Representative": [
            r"\bsdr\b",
            r"\bsales development representative\b",
        ],
}

# True: a role keyword anywhere in the posting counts (original behavior).
# False: only the title counts. False is stricter and avoids matching postings that
# merely say "you will work with solutions engineers" in the body.
MATCH_ROLE_IN_DESCRIPTION = True

# Non-technical GTM and sales titles. Checked against the title only.
EXCLUDE_TITLE_RULES = [
    r"\bbdr\b",
    r"\bbusiness development\b",
    r"\baccount executive\b",
    r"\brevenue operations\b",
    r"\brevops\b",
    r"\bsales operations\b",
    r"\bmarketing\b",
    r"\bdemand gen",
    r"\brecruit",
]

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

# Applied to the TITLE only. Descriptions say things like "work with senior
# engineers" or "report to the hiring manager" on entry-level postings too.
SENIOR_RULES = [
    r"(?<!\w)sr\.?(?!\w)",
    r"\bsenior\b",
    r"\bstaff\b",
    r"\bprincipal\b",
    r"\blead\b(?!\s*gen)",
    r"\bmanager\b",
    r"\bmgr\b",
    r"\bdirector\b",
    r"\bhead of\b",
    r"\bvice president\b",
    r"\bvp\b",
    r"\bdistinguished\b",
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
    role_text = text if MATCH_ROLE_IN_DESCRIPTION else title.lower()

    categories = []
    for category, rules in ROLE_RULES.items():
        if _matches(role_text, rules):
            categories.append(category)

    early_hits = []
    for label, rule in EARLY_RULES:
        if re.search(rule, text, re.I):
            early_hits.append(label)

    remote = bool(_matches(text, REMOTE_RULES)) or "remote" in location.lower()

    title_senior = bool(_matches(title.lower(), SENIOR_RULES))
    title_excluded = bool(_matches(title.lower(), EXCLUDE_TITLE_RULES))

    score = 0
    if categories:
        score += 10
    score += min(len(early_hits) * 4, 12)
    if remote:
        score += 2
    if re.search(r"\bbachelor'?s\b|\bcomputer science\b|\bengineering degree\b", text, re.I):
        score += 1
    if title_senior:
        score -= 20

    early_career = bool(early_hits) and not title_senior
    relevant = bool(categories) and not title_senior and not title_excluded

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
