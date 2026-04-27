import json
from pathlib import Path

import pytest

from infrastructure.openwebui_client import (
    DEFAULT_SYSTEM_PROMPT_PATH,
    PROJECT_ROOT,
    OpenWebUIClient,
)


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
        "First, extract the acceptance criteria from ticket.acceptance_criteria. "
        "If ticket.acceptance_criteria is empty, extract the acceptance criteria from ticket.description. "
        "Treat any text under or after an 'Acceptance Criteria' heading in the description as acceptance criteria. "
        "Then compare the PR diff against those acceptance criteria and ticket intent. "
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


def test_resolve_system_prompt_path_uses_default(monkeypatch):
    monkeypatch.setattr(
        "infrastructure.openwebui_client.config.PRCLOSURE_PROMPT_FILE",
        None,
    )

    path = OpenWebUIClient._resolve_system_prompt_path()

    assert path == DEFAULT_SYSTEM_PROMPT_PATH


def test_resolve_system_prompt_path_uses_relative_configured_path(monkeypatch):
    monkeypatch.setattr(
        "infrastructure.openwebui_client.config.PRCLOSURE_PROMPT_FILE",
        "prompts/custom_review_prompt.txt",
    )

    path = OpenWebUIClient._resolve_system_prompt_path()

    assert path == PROJECT_ROOT / "prompts" / "custom_review_prompt.txt"


def test_resolve_system_prompt_path_uses_absolute_configured_path(
        monkeypatch,
        tmp_path: Path,
):
    configured_path = tmp_path / "custom_review_prompt.txt"

    monkeypatch.setattr(
        "infrastructure.openwebui_client.config.PRCLOSURE_PROMPT_FILE",
        str(configured_path),
    )

    path = OpenWebUIClient._resolve_system_prompt_path()

    assert path == configured_path


def test_load_system_prompt_raises_clear_error_for_missing_file(
        monkeypatch,
        tmp_path: Path,
):
    missing_path = tmp_path / "missing_prompt.txt"

    monkeypatch.setattr(
        "infrastructure.openwebui_client.config.PRCLOSURE_PROMPT_FILE",
        str(missing_path),
    )

    with pytest.raises(RuntimeError, match="System prompt file not found"):
        OpenWebUIClient._load_system_prompt()


def test_load_system_prompt_reads_configured_file(monkeypatch, tmp_path: Path):
    prompt_path = tmp_path / "custom_review_prompt.txt"
    prompt_path.write_text("Custom prompt text", encoding="utf-8")

    monkeypatch.setattr(
        "infrastructure.openwebui_client.config.PRCLOSURE_PROMPT_FILE",
        str(prompt_path),
    )

    prompt = OpenWebUIClient._load_system_prompt()

    assert prompt == "Custom prompt text"
