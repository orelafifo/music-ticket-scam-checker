from scam_checker.privacy.names import redact_names

from .conftest import FakeNameFinder


def test_seller_called_taylor_removed_but_taylor_swift_kept(spacy_name_finder):
    text = "Hi, I'm Taylor, the seller. I have 2 Taylor Swift tickets."
    cleaned, removed = redact_names(text, artist="Taylor Swift", name_finder=spacy_name_finder)
    assert cleaned == "Hi, I'm [name], the seller. I have 2 Taylor Swift tickets."
    assert removed == 1


def test_artist_kept_despite_small_spelling_difference():
    text = "Selling Taylor Swfit tickets"
    cleaned, removed = redact_names(text, "Taylor Swift", FakeNameFinder("Taylor Swfit"))
    assert cleaned == text
    assert removed == 0


def test_artist_kept_with_accent_difference():
    cleaned, _ = redact_names("Beyonce tickets", "Beyoncé", FakeNameFinder("Beyonce"))
    assert cleaned == "Beyonce tickets"


def test_payment_word_mistaken_for_a_name_is_kept():
    # spaCy's small model really does tag "Monzo" as a person.
    cleaned, removed = redact_names("pay via Monzo please", "Tems", FakeNameFinder("Monzo"))
    assert cleaned == "pay via Monzo please"
    assert removed == 0


def test_venue_mistaken_for_a_name_is_kept():
    cleaned, _ = redact_names("2 tickets for Wembley", "Coldplay", FakeNameFinder("Wembley"))
    assert cleaned == "2 tickets for Wembley"


def test_every_other_name_is_replaced():
    cleaned, removed = redact_names("Sarah Jones and Mike", "Dave", FakeNameFinder("Sarah Jones", "Mike"))
    assert cleaned == "[name] and [name]"
    assert removed == 2
