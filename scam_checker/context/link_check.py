"""Check whether a listing's website looks fake or dodgy, WITHOUT opening it.

Visiting an unknown link could expose the user (or our server) to malware,
can warn the scammer that someone is checking, and scam sites often show a
harmless page to automated visitors anyway. So we only look at the address
itself and at public records about it.

Carried over from v2 (channels.py), tidied up, with more checks added.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Callable
from urllib.parse import urlparse

from . import website_records
from .known_sites import BRAND_WORDS, KNOWN_SITES, LINK_SHORTENERS, RISKY_ENDINGS, TWO_PART_ENDINGS

LOOKALIKE_SIMILARITY = 0.85
SHORTEST_NAME_FOR_LOOKALIKE = 5  # shorter names like "axs" or "dice" give false alarms
NEW_WEBSITE_DAYS = 180


@dataclass(frozen=True)
class WebsiteLookups:
    """The public-record lookups to use. Tests swap in fakes; None switches a lookup off."""

    domain_age_days: Callable[[str], int | None] | None = website_records.lookup_domain_age_days
    certificate_age_days: Callable[[str], int | None] | None = website_records.lookup_certificate_age_days
    on_blocklist: Callable[[str], bool | None] | None = website_records.lookup_on_blocklist


NO_LOOKUPS = WebsiteLookups(None, None, None)


@dataclass
class LinkReport:
    domain: str
    site_category: str | None = None  # official / secondary / social / unknown_site
    site_name: str | None = None
    imitates: str | None = None
    is_insecure: bool = False
    is_shortened: bool = False
    has_risky_ending: bool = False
    on_blocklist: bool | None = None  # None = not checked
    age_days: int | None = None
    certificate_age_days: int | None = None
    notes: list[str] = field(default_factory=list)
    developer_notes: list[str] = field(default_factory=list)  # shown only in developer mode

    @property
    def is_new_website(self) -> bool:
        known_ages = [age for age in (self.age_days, self.certificate_age_days) if age is not None]
        return any(age < NEW_WEBSITE_DAYS for age in known_ages)


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


def check_link(url: str, lookups: WebsiteLookups | None = None) -> LinkReport:
    lookups = lookups or WebsiteLookups()
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
        _describe_unknown_site(report, lookups)
    if report.is_insecure:
        report.notes.append("The link isn't secure (http, not https).")
    return report


def _describe_known_site(report: LinkReport) -> None:
    report.site_category, report.site_name = KNOWN_SITES[report.domain]
    report.notes.append(f"Recognised site: {report.site_name}.")


def _describe_shortened_link(report: LinkReport) -> None:
    report.site_category = "unknown_site"
    report.notes.append("Shortened link: it hides the real website. Ask for the full link.")


def _describe_unknown_site(report: LinkReport, lookups: WebsiteLookups) -> None:
    report.site_category = "unknown_site"
    _check_address(report)
    _check_public_records(report, lookups)


def _check_address(report: LinkReport) -> None:
    report.imitates = find_imitated_brand(report.domain)
    if report.imitates:
        report.notes.append(f"'{report.domain}' looks like a copy of {report.imitates}, but isn't their real website.")
    else:
        report.notes.append(f"'{report.domain}' isn't a ticket site we recognise.")
    ending = report.domain.rsplit(".", 1)[-1]
    report.has_risky_ending = ending in RISKY_ENDINGS
    if report.has_risky_ending:
        report.notes.append(f"Addresses ending in .{ending} are often used by scam sites.")
        report.developer_notes.append(f"Risky ending .{ending}: on its own this proves nothing (MEDIUM, 1 point).")


def _check_public_records(report: LinkReport, lookups: WebsiteLookups) -> None:
    report.on_blocklist = _run(lookups.on_blocklist, report.domain)
    if report.on_blocklist:
        report.notes.append("Google lists this website as a scam or dangerous site.")
    report.age_days = _run(lookups.domain_age_days, report.domain)
    if report.age_days is not None:
        report.notes.append(f"This web address was registered {report.age_days} days ago.")
    report.certificate_age_days = _run(lookups.certificate_age_days, report.domain)
    if report.certificate_age_days is not None:
        report.notes.append(f"Its first security certificate was issued {report.certificate_age_days} days ago.")


def _run(lookup, domain: str):
    return lookup(domain) if lookup else None
