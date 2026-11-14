"""Look up public records about a website, without ever opening the website itself.

Every lookup sends only the website's address (e.g. "ticket-deals.shop"), never
the full link: the rest of a link can contain an ID tied to the person checking.
If a lookup fails (offline, slow, no key), it returns None and is simply skipped.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import requests

LOOKUP_TIMEOUT_SECONDS = 8
RDAP_URL = "https://rdap.org/domain/{domain}"
CERTIFICATE_LOG_URL = "https://crt.sh/"
SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
SAFE_BROWSING_KEY_SETTING = "GOOGLE_SAFE_BROWSING_KEY"
SAFE_BROWSING_THREATS = ["SOCIAL_ENGINEERING", "MALWARE", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"]


def days_since(timestamp: str) -> int:
    moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - moment).days


def lookup_domain_age_days(domain: str) -> int | None:
    """Days since the website's address was registered, from the public RDAP registry."""
    try:
        response = requests.get(RDAP_URL.format(domain=domain), timeout=LOOKUP_TIMEOUT_SECONDS)
        response.raise_for_status()
        events = response.json().get("events", [])
        registered = next(event["eventDate"] for event in events if event.get("eventAction") == "registration")
        return days_since(registered)
    except Exception:
        return None


def lookup_certificate_age_days(domain: str) -> int | None:
    """Days since the website's first security certificate (the padlock) was issued.

    Every certificate is recorded in public logs, searchable at crt.sh. A very
    new first certificate means the website itself is new, even if its
    address was bought years ago.
    """
    try:
        params = {"q": domain, "output": "json"}
        response = requests.get(CERTIFICATE_LOG_URL, params=params, timeout=LOOKUP_TIMEOUT_SECONDS)
        response.raise_for_status()
        first_issued = min(certificate["not_before"] for certificate in response.json())
        return days_since(first_issued)
    except Exception:
        return None


def lookup_on_blocklist(domain: str) -> bool | None:
    """True if Google Safe Browsing lists the website as a scam or dangerous. None if not checked."""
    api_key = os.getenv(SAFE_BROWSING_KEY_SETTING)
    if not api_key:
        return None
    try:
        response = requests.post(
            SAFE_BROWSING_URL, params={"key": api_key}, json=_blocklist_request(domain), timeout=LOOKUP_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        return bool(response.json().get("matches"))
    except Exception:
        return None


def _blocklist_request(domain: str) -> dict:
    return {
        "client": {"clientId": "music-ticket-scam-checker", "clientVersion": "3.0"},
        "threatInfo": {
            "threatTypes": SAFE_BROWSING_THREATS,
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": f"http://{domain}/"}, {"url": f"https://{domain}/"}],
        },
    }
