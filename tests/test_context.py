from domain.services import build_context


def test_build_context():
    pr = {
        "id": 1,
        "branch": "b",
        "title": "t",
        "diff": "d",
    }

    ticket = {
        "key": "X",
        "summary": "s",
        "description": "d",
        "acceptance_criteria": "must validate output contract",
    }

    ctx = build_context(pr, ticket)

    assert ctx["pr"]["pr_id"] == 1
    assert ctx["ticket"]["key"] == "X"
    assert ctx["ticket"]["description"] == "d"
    assert ctx["ticket"]["acceptance_criteria"] == "must validate output contract"
