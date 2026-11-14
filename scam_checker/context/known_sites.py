"""Web addresses the link check recognises. Add new sites here; no other code needs to change.

Categories:
  official   - the main ticket seller, or face-value resale with buyer protection
  secondary  - open resale marketplaces (buyer guarantees, but often above face value)
  social     - social media, messaging apps and classified ads (no buyer protection)
"""

KNOWN_SITES: dict[str, tuple[str, str]] = {
    # official and face-value resale
    "ticketmaster.co.uk": ("official", "Ticketmaster"),
    "ticketmaster.com": ("official", "Ticketmaster"),
    "livenation.co.uk": ("official", "Live Nation"),
    "axs.com": ("official", "AXS"),
    "seetickets.com": ("official", "See Tickets"),
    "dice.fm": ("official", "DICE"),
    "twickets.live": ("official", "Twickets"),
    "twickets.co.uk": ("official", "Twickets"),
    "skiddle.com": ("official", "Skiddle"),
    "gigantic.com": ("official", "Gigantic"),
    "eventim.co.uk": ("official", "Eventim"),
    "ticketweb.uk": ("official", "TicketWeb"),
    "gigsandtours.com": ("official", "Gigs and Tours"),
    # secondary marketplaces
    "viagogo.co.uk": ("secondary", "viagogo"),
    "viagogo.com": ("secondary", "viagogo"),
    "stubhub.co.uk": ("secondary", "StubHub"),
    "stubhub.com": ("secondary", "StubHub"),
    "gigsberg.com": ("secondary", "Gigsberg"),
    "seatgeek.com": ("secondary", "SeatGeek"),
    "vividseats.com": ("secondary", "Vivid Seats"),
    # social media, messaging and classified ads
    "instagram.com": ("social", "Instagram"),
    "facebook.com": ("social", "Facebook"),
    "fb.com": ("social", "Facebook"),
    "x.com": ("social", "X"),
    "twitter.com": ("social", "X"),
    "tiktok.com": ("social", "TikTok"),
    "reddit.com": ("social", "Reddit"),
    "discord.com": ("social", "Discord"),
    "discord.gg": ("social", "Discord"),
    "whatsapp.com": ("social", "WhatsApp"),
    "wa.me": ("social", "WhatsApp"),
    "t.me": ("social", "Telegram"),
    "snapchat.com": ("social", "Snapchat"),
    "gumtree.com": ("social", "Gumtree"),
}

LINK_SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "cutt.ly",
    "rebrand.ly",
    "shorturl.at",
    "tiny.cc",
    "rb.gy",
}

# Brand words scammers copy into fake web addresses.
BRAND_WORDS = [
    "ticketmaster",
    "livenation",
    "seetickets",
    "twickets",
    "skiddle",
    "viagogo",
    "stubhub",
    "eventim",
    "gigantic",
    "theo2",
    "wembley",
]

# Endings where the main domain has three parts, e.g. ticketmaster.co.uk.
TWO_PART_ENDINGS = {"co.uk", "org.uk", "ac.uk", "com.au", "co.nz", "co.za", "com.br"}
