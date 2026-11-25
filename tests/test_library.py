from scam_checker.scoring.library import Library, LibraryExample


def make_library() -> Library:
    return Library(
        [
            LibraryExample("E1", "Forum A", "Bank transfer only, Oasis tickets, pay now", ("bank_transfer",), ()),
            LibraryExample("E2", "Forum A", "Oasis tickets, bank transfer please", ("bank_transfer",), ()),
            LibraryExample(
                "E3", "Blog B", "Ticketmaster transfer, PayPal goods and services", ("official_transfer",), ()
            ),
            LibraryExample("E4", "Blog C", "Paper tickets posted recorded delivery", (), ("pay_first",)),
        ]
    )


def test_finds_the_most_similar_listing_first():
    found = make_library().similar("Oasis tickets, bank transfer only", count=2)
    assert found[0].id in {"E1", "E2"}


def test_fairness_rule_skips_the_tested_example_and_its_source():
    found = make_library().similar("Oasis tickets, bank transfer only", skip_id="E1", skip_source="Forum A")
    assert all(example.source != "Forum A" for example in found)


def test_real_library_loads_with_known_questions():
    from scam_checker.scoring.questions import QUESTION_IDS

    library = Library.load()
    assert len(library.examples) >= 30
    for example in library.examples:
        assert set(example.yes) | set(example.unclear) <= set(QUESTION_IDS)
