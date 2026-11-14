"""Check a listing's web address WITHOUT opening it.

Visiting an unknown link could expose the user (or our server) to malware,
and we don't need the page. We only look at the address itself, plus the
public registration date of the website's domain.

Carried over from v2 (channels.py) and tidied up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Callable
from urllib.parse import urlparse

from .known_sites import BRAND_WORDS, KNOWN_SITES, LINK_SHORTENERS, TWO_PART_ENDINGS

LOOKALIKE_SIMILARITY = 0.85
SHORTEST_NAME_FOR_LOOKALIKE = 5  # shorter names like "axs" or "dice" give false alarms
NEW_WEBSITE_DAYS = 180
RDAP_URL = "https://rdap.org/domain/{domain}"

DomainAgeLookup = Callable[[str], "int | None"]


@dataclass
class LinkReport:
    domain: str
    site_category: str | None = None  # official / secondary / social / unknown_site
    site_name: str | None = None
    imitates: str | None = None
    is_insecure: bool = False
    is_shortened: bool = False
    age_days: int | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def is_new_website(self) -> bool:
        return self.age_days is not None and self.age_days < NEW_WEBSITE_DAYS


def split_link(url: str) -> tuple[str, str]:
    """Returns (scheme, main domain), e.g. ('https', 'ticketmaster.co.uk')."""
    url = url.strip()
    has_scheme = bool(re.match(r"^[a-z]+://", url, re.IGNORECASE))
    parsed = urlparse(url if has_scheme else "https://" + url)
    host_parts = (parsed.hostname or "").lower().rstrip(".").split(".")
    parts_to_keep = 3 if ".".join(host_parts[-2:]) in TWO_PART_ENDINGS else 2
    return parsed.scheme.lower(), ".".join(host_parts[-parts_to_keep:])


def find_imitated_brand(domain: str) -> str | None:
    """Catches 'ticketmaster-uk-sale.com' (brand word inside) and 'ticketrnaster.co.uk' (spelling trick)."""
    if domain in KNOWN_SITES:
        return None
    name = domain.split(".")[0]
    # Compare the whole name and each hyphenated piece: "ticketrnaster-uk" hides its trick in one piece.
    pieces = {name.replace("-", ""), *name.split("-")}
    for piece in pieces:
        if imitated := _closest_known_site(piece):
            return imitated
    joined = name.replace("-", "")
    return next((brand for brand in BRAND_WORDS if brand in joined), None)


def _closest_known_site(name_piece: str) -> str | None:
    for known_domain, (_category, site_name) in KNOWN_SITES.items():
        known_name = known_domain.split(".")[0]
        long_enough = len(known_name) >= SHORTEST_NAME_FOR_LOOKALIKE
        if long_enough and SequenceMatcher(None, name_piece, known_name).ratio() >= LOOKALIKE_SIMILARITY:
            return site_name
    return None


def lookup_domain_age_days(domain: str, timeout_seconds: float = 5) -> int | None:
    """Days since the domain was registered, from the public RDAP registry. None if unknown."""
    try:
        import requests

        response = requests.get(RDAP_URL.format(domain=domain), timeout=timeout_seconds)
        response.raise_for_status()
        return _registration_age_days(response.json())
    except Exception:  # offline, unknown domain, odd reply: the check is simply skipped
        return None


def _registration_age_days(rdap_reply: dict) -> int | None:
    for event in rdap_reply.get("events", []):
        if event.get("eventAction") == "registration":
            registered = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - registered).days
    return None


def check_link(url: str, lookup_age: DomainAgeLookup | None = lookup_domain_age_days) -> LinkReport:
    scheme, domain = split_link(url)
    report = LinkReport(domain=domain, is_insecure=scheme == "http", is_shortened=domain in LINK_SHORTENERS)
    if "." not in domain:
        report.notes.append("That doesn't look like a valid web address.")
        return report
    if domain in KNOWN_SITES:
        _describe_known_site(report)
    elif report.is_shortened:
        _describe_shortened_link(report)
    else:
        _describe_unknown_site(report, lookup_age)
    if report.is_insecure:
        report.notes.append("The link isn't secure (http, not https).")
    return report


def _describe_known_site(report: LinkReport) -> None:
    report.site_category, report.site_name = KNOWN_SITES[report.domain]
    report.notes.append(f"Recognised site: {report.site_name}.")


def _describe_shortened_link(report: LinkReport) -> None:
    report.site_category = "unknown_site"
    report.notes.append("Shortened link: it hides the real website. Ask for the full link.")


def _describe_unknown_site(report: LinkReport, lookup_age: DomainAgeLookup | None) -> None:
    report.site_category = "unknown_site"
    report.imitates = find_imitated_brand(report.domain)
    if report.imitates:
        report.notes.append(f"'{report.domain}' looks like a copy of {report.imitates}, but isn't their real website.")
    else:
        report.notes.append(f"'{report.domain}' isn't a ticket site we recognise.")
    report.age_days = lookup_age(report.domain) if lookup_age else None
    if report.age_days is not None:
        report.notes.append(f"This website was registered {report.age_days} days ago.")
