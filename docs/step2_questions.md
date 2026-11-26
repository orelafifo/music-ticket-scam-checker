# Step 2: yes/no questions the AI answers (approved by Orela, 23 Nov 2026)

Drafted 23 Nov 2026 from published UK guidance. The AI reads the cleaned listing or chat and answers each question **yes / no / unclear**. It never says "scam" or "not scam". The scoring learns how much each answer matters.

Things Step 1 already covers are **not** repeated here (where the tickets were found, how you met the seller, the seller's account, the website check, the event check).

## Red flags (a "yes" points towards a scam)
| # | Question the AI is asked | Source |
|---|---|---|
| 1 | Does the seller ask for payment by bank transfer? | Take Five: the seller wants payment by bank transfer rather than a secure method. https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/ |
| 2 | Does the seller ask for PayPal "Friends and Family"? | PayPal UK: Friends and Family payments are not covered by Buyer Protection. https://paypal.com/uk/security/learn-about-scams |
| 3 | Does the seller ask for another payment with no protection (gift cards, crypto, Western Union, cash sent in advance)? | Aura (US): never wire funds or pay by gift cards for tickets. https://aura.com/learn/ticketmaster-scams (weaker: US source) |
| 4 | Does the seller want the money before the tickets are sent? | Get Safe Online (via Croydon Council): the seller says they'll post or email the tickets once the money is transferred. https://news.croydon.gov.uk/trading-standards-advise-residents-not-to-fall-victim-to-ticket-scams-during-uefa-euro-2024 |
| 5 | Does the seller ask for part of the money now (a deposit, half now, instalments)? | MoneySavingExpert: a buyer of The 1975 tickets agreed to pay in instalments; the seller insisted on Friends and Family. https://blog.moneysavingexpert.com/news/2020/03/paypal-scam-victims-warn-against-fraudsters-who-ask-for--family- |
| 6 | Does the seller ask you to pay into someone else's account (a friend, partner, relative, colleague), or say the name won't match? | Leicestershire Police (2025): a victim paid into an account in a different name to the seller. https://www.leics.police.uk/news/leicestershire/news/2025/april/warning-to-people-buying-concert-tickets-via-social-media/ ; Virgin Money on Confirmation of Payee. https://uk.virginmoney.com/service/cop/ |
| 7 | After agreeing a price, does the seller ask for more money (a fee, name change, delivery)? | Hackettstown Police (US), via CBS: the victim paid, the seller asked for more money and never sent the tickets. https://cbsnews.com/newyork/news/taylor-swift-ticket-scam-new-jersey (weaker: US source) |
| 8 | Does the seller pressure you to pay quickly (others interested, "today only")? | Take Five (above); Lloyds Bank: "somebody else wants to buy now". https://www.lloydsbank.com/help-guidance/protecting-yourself-from-fraud/ticket-scams.html |
| 9 | Is the price described as very cheap, or far below what tickets normally cost? | Take Five: the ticket is far cheaper than similar tickets elsewhere (above) |
| 10 | Does the seller give a sad or personal reason for selling (illness, break-up, family problem)? | North West Regional Organised Crime Unit: criminals prey on emotions, e.g. a sob story. https://www.rocu.police.uk/syssiteassets2/media/images/news/nwrocu/nwrocu_lbobs_5th-edition_rgb_2025-online.pdf |
| 11 | Does the seller ask you to message them privately (DM, PM, inbox) or move to WhatsApp? | Lloyds Bank (2026): criminals advertise a ticket, then shift the conversation to WhatsApp. https://www.lloydsbank.com/media-centre/2026/football-fans-urged-to-show-fraudsters-the-red-card.html |
| 12 | Does the seller offer a screenshot or photo as proof that they have the tickets? | An Post: fraudsters provide screenshots of tickets and receipts to prove they are real. https://www.anpost.com/Money/Managing-Finances/Blog/How-To-Spot-Concert-Ticket-Scams |
| 13 | Does the seller offer the ticket as a PDF, screenshot or printout? | Ticketmaster: screenshots of mobile tickets will not be accepted for entry. https://help.ticketmaster.com/hc/en-us/articles/9611493057425-Can-I-print-my-mobile-ticket-and-take-the-paper-ticket-to-get-in |
| 14 | Does the seller avoid giving clear details (date, venue, seats, booking confirmation)? | Take Five: the seller won't give clear booking details, seat information or confirmation from an official ticket provider (above) |
| 15 | Does the seller suggest meeting outside the venue to hand over the tickets? | Take Five: you're told someone will meet you outside the venue with the ticket (above) |
| 16 | Does the seller refuse a phone or video call? | Refundee (2026): the seller avoids phone or video calls. https://www.refundee.com/blog/ticket-scams-uk (weaker: commercial site) |
| 17 | Is it a giveaway or competition asking you to like, share, comment or pay a fee? | Which?: fake ticket giveaways and competitions are rife on social media. https://www.which.co.uk/news/article/five-tips-to-avoid-tickets-scams-and-dud-deals-aDALz5M722Ld |

## Good signs (a "yes" points towards a genuine sale)
| # | Question | Source |
|---|---|---|
| 18 | Does the seller offer to sell or transfer through an official site or app (Ticketmaster, Twickets, AXS, DICE)? | Take Five: buy only from official sellers and recognised resale platforms (above) |
| 19 | Does the seller offer a protected way to pay (PayPal Goods and Services, card)? | PayPal UK: Goods and Services payments can be covered by Buyer Protection (above) |
| 20 | Is a price given openly in the listing? | Linked to Take Five's "clear details" sign (above); a judgement call |

## Decisions
- [x] Approved by Orela, 23 Nov 2026. Question 18 ("100% legit") dropped: no source.
- [ ] Replace the 3 weaker sources (3, 7, 16) if better UK ones turn up

## Prompt version 2 (context engineering, 24 Nov 2026)
Changes made after the first comparison, to cut false alarms and catch fake 'official' messages. They fix what the AI misread in the text; things Step 1 covers (where the tickets were found, how you met the seller, website and event checks) are left to Step 1. Version 1 is kept in the code (`V1_QUESTIONS`) so it can be re-run.

| Question | Change |
|---|---|
| Sad story (10) | Any personal story or reason (illness, family, a baby, exams, work, money); a plain "can't go any more" is no |
| Bank transfer (1) | No if only offered as an option next to an official transfer or protected payment |
| No clear details (14) | Yes if none of seat, row, section, standing or festival ticket type is given; any one is enough for no; a date and venue alone is still yes (26 Nov) |
| **Removed: specific details (21)** | 26 Nov: with the new meaning it was the exact opposite of no clear details, and the AI often left it out of its reply. 21 questions now |
| Official transfer (18) | Yes if they mention transferring through Ticketmaster, AXS, DICE, See Tickets, Twickets, or the venue's or festival's own resale |
| Other unprotected payment (3) | Not bank transfer (a separate question) |
| Screenshot as proof (12) | Only when offered as proof, not as the ticket itself |
| **New good sign (21)**: "Does the seller give specific ticket details (date, venue, section, row or seat)?" | Take Five: clear booking details, seat information |
| PDF or screenshot ticket (13) | Only the ticket itself as a PDF, screenshot or printout; posting paper tickets or an official e-ticket is no |
| Part payment (5) | Only when the seller asks you to pay part first; their own deposit is no |
| Very cheap (9) | Only unrealistically cheap (e.g. under half face value); a small discount is no |
| Pressure to pay (8) | Urging you to pay quickly, including "quick sale"; asking for offers is no |
| Move to private chat (11) | Email added |
| Official transfer (18) | Also: a message claiming to BE a ticket company is not this |
| Protected payment (20) | Plain "PayPal" with no detail is unclear |
| **New red flag (22)**: "Does the message claim to be from a ticket company or resale team and ask you to pay or confirm through a link, a message or a bank transfer?" | Twickets founder via PA/STV (2025): fake Twickets accounts and websites. https://news.stv.tv/world/music-fans-urged-to-be-wary-of-last-minute-glastonbury-and-oasis-offers |

The prompt also gives 7 short worked examples, written for the prompt (not taken from the practice or test data). See `EXAMPLES` in `scam_checker/scoring/ask_ai.py`.

