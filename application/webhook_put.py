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


def _format_qa_checklist_old(items: list[QAChecklistItem]) -> str:
    if not items:
        return "No additional QA checks required."

    blocks = []

    for item in items:
        steps = "\n".join(
            f"  - {step}"
            for step in item.steps
        )

        blocks.append(
            (
                f"- [ ] {item.title}\n"
                f"  Acceptance criteria: {item.acceptance_criteria_ref}\n"
                f"  Steps:\n"
                f"{steps}\n"
                f"  Expected result: {item.expected_result}"
            )
        )

    return "\n\n".join(blocks)


def _format_qa_checklist(items: list[QAChecklistItem]) -> str:
    if not items:
        return (
            "Reviewed the PR against the ticket.\n\n"
            "Validated:\n"
            "- No additional acceptance-criteria-specific QA checks were identified from the automated review.\n\n"
            "Observed:\n"
            "- Nothing in the review output highlighted extra behavioural risk for QA.\n\n"
            "Outcome:\n"
            "- No gaps identified by PRClosure.\n\n"
            "QA Action:\n"
            "- Run standard checks and confirm behaviour against the ticket acceptance criteria."
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
