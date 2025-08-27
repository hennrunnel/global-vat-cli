import re
from typing import Iterable, List

import feedparser


KEYWORDS = [
    "VAT",
    "GST",
    "rate change",
    "indirect tax",
    "HST",
    "PST",
]

COUNTRY_HINTS = [
    "Austria",
    "United Kingdom",
    "UK",
    "Canada",
    "Switzerland",
    "Norway",
    "EU",
]


SOURCES = [
    # EY Cross-Border Taxation Alerts (podcast feed)
    "https://podcasts.apple.com/us/podcast/ey-cross-border-taxation-alerts/id594960922",
    # Deloitte updates (may not be a true RSS feed; feedparser will handle gracefully)
    "https://taxscape.deloitte.com/home/updates.aspx",
]


def _match_entry(title: str, summary: str) -> bool:
    text = f"{title} {summary}" if summary else title
    return any(re.search(rf"\b{re.escape(kw)}\b", text, flags=re.IGNORECASE) for kw in KEYWORDS) and any(
        re.search(rf"\b{re.escape(ch)}\b", text, flags=re.IGNORECASE) for ch in COUNTRY_HINTS
    )


def run_monitor() -> None:
    alerts: List[str] = []
    for src in SOURCES:
        try:
            feed = feedparser.parse(src)
            if getattr(feed, "bozo_exception", None):
                # Not a valid RSS/Atom; skip silently
                continue
            for entry in feed.entries[:25]:
                title = getattr(entry, "title", "")
                summary = getattr(entry, "summary", "")
                if _match_entry(title, summary):
                    alerts.append(f"ALERT: Potential VAT/GST change mentioned in source: {title} -> {src}")
        except Exception:
            # Non-fatal
            continue

    if not alerts:
        print("No alerts found in monitoring sources.")
    else:
        for a in alerts:
            print(a)


