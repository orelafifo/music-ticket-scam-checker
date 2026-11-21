import pytest

from scam_checker.privacy.patterns import redact_patterns


@pytest.mark.parametrize(
    ("text", "expected", "kind"),
    [
        ("email me at jess.smith@gmail.com", "email me at [email]", "email"),
        ("follow @ticketqueen_99 for more", "follow [handle] for more", "handle"),
        ("call 07123 456789", "call [phone]", "phone number"),
        ("call +44 7123 456789", "call [phone]", "phone number"),
        ("sort code 12-34-56", "sort code [sort code]", "sort code"),
        ("sort code 123456", "sort code [sort code]", "sort code"),
        ("account 12345678", "account [account number]", "account number"),
        ("card 4111 1111 1111 1111", "card [card number]", "card number"),
    ],
)
def test_personal_details_are_removed(text, expected, kind):
    cleaned, removed = redact_patterns(text)
    assert cleaned == expected
    assert removed[kind] == 1


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("~ Me\nstill got the tickets", "~[name]\nstill got the tickets"),
        ("~Megan 💜💖💜\nhey guys", "~[name]\nhey guys"),
        ("~Oreoluwa: bank transfer only", "~[name]: bank transfer only"),
        (
            "~Zayba anyone want 2 Taylor Swift tickets for Wembley tonight",
            "~[name] anyone want 2 Taylor Swift tickets for Wembley tonight",
        ),
    ],
)
def test_whatsapp_display_name_after_tilde_is_removed(text, expected):
    cleaned, removed = redact_patterns(text)
    assert cleaned == expected
    assert removed["name"] == 1


def test_x_post_header_display_name_is_removed():
    cleaned, removed = redact_patterns("Megan 💜 @megs_tix · 2h\nSelling 2 for Wembley")
    assert cleaned == "[name] [handle] · 2h\nSelling 2 for Wembley"
    assert removed == {"name": 1, "handle": 1}


def test_message_mentioning_a_handle_keeps_its_words():
    cleaned, _ = redact_patterns("DM me @megs_tix for the tickets")
    assert cleaned == "DM me [handle] for the tickets"


def test_tilde_inside_a_line_is_left_alone():
    assert redact_patterns("£80 each ~ish")[0] == "£80 each ~ish"


def test_payment_link_keeps_the_service_but_hides_the_username():
    cleaned, _ = redact_patterns("send it to paypal.me/jessica123")
    assert cleaned == "send it to paypal.me/[handle]"


@pytest.mark.parametrize(
    "text",
    [
        "PayPal friends and family only",
        "Revolut or Monzo is fine",
        "Transfer through Ticketmaster or Twickets, AXS also works",
        "£85 each, 2 tickets, Block 112 Row K",
        "Show on 14/11/2026",
    ],
)
def test_warning_signs_and_listing_details_are_kept(text):
    cleaned, removed = redact_patterns(text)
    assert cleaned == text
    assert not removed
