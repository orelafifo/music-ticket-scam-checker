# Step 2: how much each Step 1 answer counts (approved by Orela, 23 Nov 2026)

Suggested by Claude on 23 Nov 2026. Approved by Orela on 23 Nov 2026. Used in `scam_checker/scoring/step1_signals.py`.

## How the points work
- Each Step 1 answer adds points to the scam score. More points = more likely a scam.
- **+2 = high risk, +1 = medium, +0.5 = low, 0 = no change, negative = lowers the risk.**
- "Not sure", "N/A" or "not checked" is always **0**. Unknown is never suspicious.
- These points are added to the points from the AI's yes/no answers (which are learned from the practice data).
- Every answer that adds points is shown to the user as a reason.

## 1. How did you come across this seller?
| Answer | Points | Reason shown to the user | Source |
|---|---|---|---|
| A stranger in a group chat | +2 | "The seller is a stranger in a group chat. Scammers join open group chats and advertise tickets straight away." | The Cheese Grater (UCL student paper): scammers joined society group chats and immediately advertised tickets. https://cheesegratermagazine.org/?p=9093 |
| A stranger messaged you first | +2 | "A stranger contacted you first with an offer." | GOV.UK (2025): key signs include unsolicited messages with ticket offers. https://www.gov.uk/government/news/16m-lost-to-gig-ticket-scams-as-public-urged-to-take-caution ; Take Five: be wary if the seller contacts you through social media or a messaging app. https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/ |
| A stranger replying to a comment or post | +1.5 | "A stranger replied to a post offering tickets." | West Mercia Police / National Crime Agency: scammers often reply to social posts from people looking for tickets. https://honeybourne-pc.gov.uk/wp-content/uploads/2024/09/WMPNLSEPT24.pdf |
| A post from someone you don't know | +1 | "The tickets are offered in a post by someone you don't know." | GOV.UK (2025): almost half of gig ticket fraud reports in 2024 referred to offers on social media. (link above) |
| An unknown website or marketplace listing | +0.5 | "The tickets are on a marketplace or website you don't know." | Willingham Parish Council, citing Cambridgeshire Police and Action Fraud: fraudsters invent ticket websites that look genuine. https://willinghamparishcouncil.gov.uk/2022/05/09/scam-in-focus-concert-ticket-scams/ (the website check adds more points if the site itself looks risky) |
| Someone you know | 0 | No points, but a tip: "Check it's really them: friends' accounts are often hacked to sell fake tickets." | Which? (2025): a hacker used a friend's Instagram to sell fake Oasis tickets. https://www.which.co.uk/news/article/a-hacker-scammed-my-friends-on-instagram-with-fake-oasis-tickets-aqNjr2u6LbJy . This is why "someone you know" does not lower the risk. |
| Not sure | 0 | (nothing) | |

## 2. Where did you find the tickets?
| Answer | Points | Reason shown | Source |
|---|---|---|---|
| WhatsApp, Instagram, TikTok, X, Facebook | +0.5 | "Most ticket scams start on social media." | Lloyds (2024): over 90% of the Oasis ticket scams it saw began with adverts on social media, mostly Facebook. https://www.aol.com/oasis-fans-hit-landslide-ticket-120228085.html |
| A forum | 0 | | |
| A website | 0 | (the website check decides) | |
| Other | 0 | | |

Low weight on purpose: "how you came across the seller" already covers most of the risk, so this avoids counting social media twice.

## 3. Seller's account
| Answer | Points | Reason shown | Source |
|---|---|---|---|
| Account younger than 6 months | +1 | "The seller's account is new." | Take Five: criminals create fake profiles to offer tickets (link above). Refundee (2026): a recently created account with little history is a warning sign. https://www.refundee.com/blog/ticket-scams-uk (a commercial site, so a weaker source) |
| Fewer than 50 followers | +0.5 | "The seller's account has very few followers." | Same as above |
| N/A | 0 | | |

The cut-offs (6 months, 50 followers) are a judgement call. Say so in the report.

## 4. Website check (only when the tickets were on a website)
| Result | Points | Reason shown | Source |
|---|---|---|---|
| On Google Safe Browsing's list of dangerous sites | **Always a warning** | "Google lists this website as dangerous." | Google Safe Browsing is Google's list of known unsafe sites. |
| Pretends to be a known ticket site (lookalike) | +2 | "The web address looks like a copy of [site]." | Willingham / Cambridgeshire Police: some fake sites use a name or address very similar to a real ticket site (link above) |
| Brand-new website | +2 | "This website was set up very recently." | **Source still needed** |
| Shortened link (bit.ly etc.) | +1 | "The link is shortened, which hides where it really goes." | **Source still needed** |
| Not secure (http) | +1 | "The website is not secure (no https)." | **Source still needed** |
| Risky ending (.shop etc.) | +1 | "The web address has an ending often used by scam sites." | **Source still needed** |
| An official ticket site (Ticketmaster, Twickets, AXS, DICE…) | −1.5 | Good sign: "This is an official ticket site." | GOV.UK (2025): use a reputable or official ticket-selling site (link above) |

## 5. Event check (same as v2, approved by Orela 23 Nov 2026)
| Result | Points | Reason shown |
|---|---|---|
| Date or venue doesn't match the official event | **Always a warning** | "The date or venue doesn't match the official event (...)." |
| PDF or screenshot offered for an app-only event | **Always a warning** | "This event uses app tickets only, but the seller offers a PDF or screenshot." |
| Offered before the official general sale | +2 | "Tickets are offered before the official general sale." |
| Event not found on official listings | +2 | "We couldn't find this event on official listings." (only if every source was searched) |
| Sold-out / high-demand show | +0.5 | "This is a sold-out show, which scammers target." |
| Not checked (no key, no internet, not listed) | 0 | |

## To decide
- [ ] Orela checks every source link
- [ ] Find sources for the 4 rows marked "source still needed"
- [x] Approve or change each number (approved 23 Nov 2026)
