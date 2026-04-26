from domain.models import LLMReviewOutput
from application import webhook_fetch


class FakeJiraClient:
    @staticmethod
    def get_ticket(key):
        return {
            "key": key,
            "summary": "Test ticket",
            "description": "Acceptance criteria: validate output contract.",
        }


class FakeGitHubClient:
    @staticmethod
    def get_pr_diff(_owner, _repo, _pr_number):
        return "diff --git a/example.py b/example.py"


class FakeOpenWebUIClient:
    def __init__(self, content):
        self.content = content

    def analyze(self, _context):
        return {
            "choices": [
                {
                    "message": {
                        "content": self.content,
                    }
                }
            ]
        }


def _payload():
    return {
        "repository": {
            "name": "olo-pr-closure",
            "owner": {
                "login": "OLO-Governor",
            },
        },
        "pull_request": {
            "id": 123,
            "number": 12,
            "title": "OPRC-3 output contract",
            "head": {
                "ref": "OPRC-3-output-contract",
            },
        },
    }


def test_invalid_llm_output_blocks_writeback(monkeypatch):
    writeback_calls = []

    def fake_writeback(*args):
        writeback_calls.append(args)

    monkeypatch.setattr(webhook_fetch, "jira_client", FakeJiraClient())
    monkeypatch.setattr(webhook_fetch, "github_client", FakeGitHubClient())
    monkeypatch.setattr(
        webhook_fetch,
        "openwebui_client",
        FakeOpenWebUIClient("## Not JSON"),
    )
    monkeypatch.setattr(webhook_fetch, "handle_writeback", fake_writeback)

    result, error = webhook_fetch.handle_webhook(_payload())

    assert error == "Invalid LLM output"
    assert result["validation_errors"] == ["LLM output is not a valid JSON object"]
    assert writeback_calls == []


def test_valid_llm_output_reaches_writeback(monkeypatch):
    writeback_calls = []

    def fake_writeback(_github_client, _jira_client, context, analysis):
        writeback_calls.append(
            {
                "context": context,
                "analysis": analysis,
            }
        )

    valid_content = """
    {
      "pr_comments": [
        {
          "file": "application/webhook_fetch.py",
          "line": 42,
          "severity": "medium",
          "category": "validation",
          "message": "Validate LLM output before write-back.",
          "rationale": "Invalid output must not reach GitHub or Jira."
        }
      ],
      "qa_checklist": [
        {
          "title": "Validate malformed LLM output is blocked",
          "steps": [
            "Return malformed JSON from the LLM",
            "Confirm write-back is blocked"
          ],
          "acceptance_criteria_ref": "OPRC-3",
          "expected_result": "No write-back occurs"
        }
      ]
    }
    """

    monkeypatch.setattr(webhook_fetch, "jira_client", FakeJiraClient())
    monkeypatch.setattr(webhook_fetch, "github_client", FakeGitHubClient())
    monkeypatch.setattr(
        webhook_fetch,
        "openwebui_client",
        FakeOpenWebUIClient(valid_content),
    )
    monkeypatch.setattr(webhook_fetch, "handle_writeback", fake_writeback)

    result, error = webhook_fetch.handle_webhook(_payload())

    assert error is None
    assert len(writeback_calls) == 1
    assert isinstance(writeback_calls[0]["analysis"], LLMReviewOutput)
    assert result["context"]["ticket"]["key"] == "OPRC-3"
