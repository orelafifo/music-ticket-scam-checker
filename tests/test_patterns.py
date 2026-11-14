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
