"""Extracts structured experience requirements from job postings.

This module only extracts and formats data. It does not decide whether a
job is acceptable -- that decision belongs to `is_over_experienced`, which
takes the structured result and a cap, and to whoever calls it.
"""
import html
import re

_TAG_RE = re.compile(r"<[^>]+>")

_YEARS_RE = re.compile(
    r"(\d{1,2})\s*(\+|(?:-|–|to)\s*(\d{1,2}))?\s*(?:or more\s*)?(?:years?|yrs?)\b",
    re.I,
)

_PREFERRED_PHRASES = (
    "preferred", "preferably", "nice to have", "nice-to-have",
    "bonus", "a plus", "desired", "ideally",
)


def _clean_text(text: str) -> str:
    # Greenhouse returns HTML-escaped HTML, so unescape, strip tags, unescape again
    text = html.unescape(text or "")
    text = _TAG_RE.sub(" ", text)
    return html.unescape(text)


def _sentence_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Start/end of the sentence containing text[start:end], so phrases from
    a neighboring sentence (e.g. a later 'preferred' clause) don't leak in."""
    s = text.rfind(".", 0, start) + 1
    e = text.find(".", end)
    return s, (e if e != -1 else len(text))


def _parse_mentions(text: str) -> list[dict]:
    """Every years-of-experience phrase found in the text, each tagged with
    whether it reads as a hard requirement or a 'nice to have'."""
    text = _clean_text(text)
    mentions = []

    for m in _YEARS_RE.finditer(text):
        s, e = _sentence_span(text, m.start(), m.end())
        sentence = text[s:e].lower()
        before = text[s: m.start()].lower()

        if "experience" not in sentence:
            continue

        low = int(m.group(1))
        high = int(m.group(3)) if m.group(3) else None
        is_plus = bool(
            m.group(2) == "+" or "or more" in before or "at least" in before or "minimum" in before
        )
        is_required = not any(phrase in sentence for phrase in _PREFERRED_PHRASES)

        mentions.append({
            "min_years": low,
            "max_years": high,
            "is_plus": is_plus,
            "is_required": is_required,
        })

    return mentions


def _effective_years(mention: dict) -> int:
    """The number that matters for comparison: the top of a range, or the
    single number for an open-ended '3+' or exact '3 years' mention."""
    return mention["max_years"] if mention["max_years"] is not None else mention["min_years"]


def parse_experience(text: str) -> dict:
    """Extract the single binding experience requirement from a posting.

    Returns {"min_years": int|None, "max_years": int|None, "is_plus": bool,
    "is_required": bool}. All fields are None/False when nothing is found.

    When both required and preferred mentions exist, the required one wins
    since that's what actually gates who can apply. Among several mentions
    of the same kind, the strictest (highest effective years) is returned.
    This is pure extraction -- it makes no accept/reject decision.
    """
    mentions = _parse_mentions(text)
    if not mentions:
        return {"min_years": None, "max_years": None, "is_plus": False, "is_required": False}

    required = [m for m in mentions if m["is_required"]]
    pool = required if required else mentions
    return max(pool, key=_effective_years)


def format_experience(exp: dict) -> str:
    """Human-readable string for display, e.g. '3+ yrs', '2-4 yrs', 'Not stated'."""
    if exp["min_years"] is None:
        return "Not stated"

    low, high = exp["min_years"], exp["max_years"]
    label = f"{low}-{high} yrs" if high else (f"{low}+ yrs" if exp["is_plus"] else f"{low} yrs")
    if not exp["is_required"]:
        label += " (preferred)"
    return label


def is_over_experienced(exp: dict, cap: int = 2) -> bool:
    """True only when the posting REQUIRES more than `cap` years. A
    preferred/bonus mention, or no mention at all, never rejects a job --
    'not stated' should not be treated as 'too senior'."""
    if not exp["is_required"] or exp["min_years"] is None:
        return False
    return _effective_years(exp) > cap
