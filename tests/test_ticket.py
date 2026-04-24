from domain.services import extract_ticket_key


def test_extract_from_branch():
    assert extract_ticket_key("OPRC-6-branch", "") == "OPRC-6"


def test_extract_from_title():
    assert extract_ticket_key("", "OPRC-9: test") == "OPRC-9"


def test_no_ticket():
    assert extract_ticket_key("feature-x", "test") is None
