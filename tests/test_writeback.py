import pytest

from application.webhook_put import handle_writeback
from domain.models import LLMReviewOutput, PRComment, QAChecklistItem


class FakeGitHubClient:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def upsert_pr_comment(self, owner, repo, pr_number, body, marker):
        self.calls.append(
            {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "body": body,
                "marker": marker,
            }
        )

        return self.ok


class FakeJiraClient:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def upsert_comment(self, issue_key, body, marker):
        self.calls.append(
            {
                "issue_key": issue_key,
                "body": body,
                "marker": marker,
            }
        )

        return self.ok


def test_handle_writeback_posts_validated_output():
    github_client = FakeGitHubClient()
    jira_client = FakeJiraClient()

    context = {
        "pr": {
            "repo_owner": "OLO-Governor",
            "repo_name": "olo-pr-closure",
            "number": 12,
        },
        "ticket": {
            "key": "OPRC-3",
        },
    }

    analysis = LLMReviewOutput(
        pr_comments=[
            PRComment(
                file="application/webhook_fetch.py",
                line=42,
                severity="medium",
                category="validation",
                message="Validate LLM output before write-back.",
                rationale="Invalid output must not reach GitHub or Jira.",
            )
        ],
        qa_checklist=[
            QAChecklistItem(
                title="Validate malformed LLM output is blocked",
                steps=[
                    "Return malformed JSON from the LLM",
                    "Confirm GitHub write-back is not called",
                    "Confirm Jira write-back is not called",
                ],
                acceptance_criteria_ref="OPRC-3",
                expected_result="Write-back is blocked",
            )
        ],
    )

    handle_writeback(
        github_client,
        jira_client,
        context,
        analysis,
    )

    assert len(github_client.calls) == 1
    assert len(jira_client.calls) == 1

    github_call = github_client.calls[0]
    jira_call = jira_client.calls[0]

    assert github_call["owner"] == "OLO-Governor"
    assert github_call["repo"] == "olo-pr-closure"
    assert github_call["pr_number"] == 12
    assert github_call["marker"] == "<!-- prclosure:OPRC-3 -->"
    assert "application/webhook_fetch.py:42" in github_call["body"]
    assert "Validate LLM output before write-back." in github_call["body"]

    assert jira_call["issue_key"] == "OPRC-3"
    assert jira_call["marker"] == "<!-- prclosure:OPRC-3 -->"
    assert "Validate malformed LLM output is blocked" in jira_call["body"]
    assert "Write-back is blocked" in jira_call["body"]


def test_handle_writeback_raises_when_github_write_fails():
    github_client = FakeGitHubClient(ok=False)
    jira_client = FakeJiraClient()

    context = {
        "pr": {
            "repo_owner": "OLO-Governor",
            "repo_name": "olo-pr-closure",
            "number": 12,
        },
        "ticket": {
            "key": "OPRC-3",
        },
    }

    analysis = LLMReviewOutput(
        pr_comments=[],
        qa_checklist=[
            QAChecklistItem(
                title="QA item",
                steps=["Run validation"],
                acceptance_criteria_ref="OPRC-3",
                expected_result="Validation passes",
            )
        ],
    )

    with pytest.raises(RuntimeError, match="GitHub write-back failed"):
        handle_writeback(
            github_client,
            jira_client,
            context,
            analysis,
        )

    assert len(github_client.calls) == 1
    assert len(jira_client.calls) == 0


def test_handle_writeback_raises_when_jira_write_fails():
    github_client = FakeGitHubClient()
    jira_client = FakeJiraClient(ok=False)

    context = {
        "pr": {
            "repo_owner": "OLO-Governor",
            "repo_name": "olo-pr-closure",
            "number": 12,
        },
        "ticket": {
            "key": "OPRC-3",
        },
    }

    analysis = LLMReviewOutput(
        pr_comments=[
            PRComment(
                file="x.py",
                line=1,
                severity="low",
                category="correctness",
                message="Review message",
                rationale="Review rationale",
            )
        ],
        qa_checklist=[],
    )

    with pytest.raises(RuntimeError, match="Jira write-back failed"):
        handle_writeback(
            github_client,
            jira_client,
            context,
            analysis,
        )

    assert len(github_client.calls) == 1
    assert len(jira_client.calls) == 1
