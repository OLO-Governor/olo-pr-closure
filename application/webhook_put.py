from domain.models import LLMReviewOutput, PRComment, QAChecklistItem


def handle_writeback(
        github_client,
        jira_client,
        context,
        analysis: LLMReviewOutput,
):
    pr = context["pr"]
    ticket = context["ticket"]

    repo_owner = pr.get("repo_owner")
    repo_name = pr.get("repo_name")
    pr_number = pr.get("number")

    marker = f"<!-- prclosure:{ticket['key']} -->"

    pr_comment_body = _format_pr_comments(analysis.pr_comments)
    qa_checklist_body = _format_qa_checklist(analysis.qa_checklist)

    github_ok = github_client.upsert_pr_comment(
        repo_owner,
        repo_name,
        pr_number,
        pr_comment_body,
        marker,
    )

    if not github_ok:
        raise RuntimeError("GitHub write-back failed")

    jira_ok = jira_client.upsert_comment(
        ticket["key"],
        qa_checklist_body,
        marker,
    )

    if not jira_ok:
        raise RuntimeError("Jira write-back failed")


def _format_pr_comments(comments: list[PRComment]) -> str:
    if not comments:
        return "No high-level PR issues identified."

    return "\n".join(
        [
            (
                f"- `{comment.file}:{comment.line}` "
                f"[{comment.severity}] "
                f"{comment.category}: {comment.message}\n"
                f"  Rationale: {comment.rationale}"
            )
            for comment in comments
        ]
    )


def _format_qa_checklist(items: list[QAChecklistItem]) -> str:
    if not items:
        return (
            "Reviewed the PR against the ticket.\n\n"
            "Validated:\n"
            "- Acceptance criteria were checked against the changes where possible from the diff.\n\n"
            "Observed:\n"
            "- No specific risks or edge cases were identified from the changes.\n\n"
            "Outcome:\n"
            "- No gaps identified from code review. Behaviour should be confirmed in QA.\n\n"
            "QA Action:\n"
            "- Verify acceptance criteria are met in a running environment.\n"
            "- Confirm no regression in related behaviour."
        )

    blocks = [
        "Reviewed the PR against the ticket.",
        "",
        "Validated:",
    ]

    for item in items:
        blocks.append(f"- {item.acceptance_criteria_ref}: {item.title}")

    blocks.extend(
        [
            "",
            "Observed:",
        ]
    )

    for item in items:
        for step in item.steps:
            blocks.append(f"- {step}")

    blocks.extend(
        [
            "",
            "Outcome:",
        ]
    )

    for item in items:
        blocks.append(f"- {item.expected_result}")

    blocks.extend(
        [
            "",
            "QA Action:",
            "- Run the checks above and confirm behaviour against the acceptance criteria.",
            "- Block progression if the observed behaviour does not match the expected result.",
        ]
    )

    return "\n".join(blocks)
