import json

from infrastructure.openwebui_client import OpenWebUIClient


def test_format_context_returns_stable_json():
    context = {
        "ticket": {
            "key": "OPRC-3",
            "description": "Define output contract.",
            "acceptance_criteria": "Output must be structured JSON.",
        },
        "pr": {
            "diff": "diff --git a/x.py b/x.py",
            "number": 12,
        },
    }

    result = OpenWebUIClient._format_context(context)

    parsed = json.loads(result)

    assert parsed["instruction"] == (
        "Review the provided PR against the provided ticket context. "
        "Return only JSON matching the required output contract."
    )
    assert parsed["context"]["ticket"]["key"] == "OPRC-3"
    assert parsed["context"]["ticket"]["acceptance_criteria"] == (
        "Output must be structured JSON."
    )
    assert result == OpenWebUIClient._format_context(context)


def test_format_context_sorts_keys():
    context = {
        "z": 1,
        "a": 2,
    }

    result = OpenWebUIClient._format_context(context)

    assert result.index('"a"') < result.index('"z"')
