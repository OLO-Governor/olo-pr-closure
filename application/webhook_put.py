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
    jira_comment_body = _format_jira_comment(analysis)

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
        jira_comment_body,
        marker,
    )

    if not jira_ok:
        raise RuntimeError("Jira write-back failed")


def _format_pr_comments(comments: list[PRComment]) -> str:
    if not comments:
        return (
            "AI-assisted diff review completed.\n\n"
            "Scope:\n"
            "- Code changes in the PR diff were reviewed against ticket intent and acceptance criteria where "
            "visible.\n\n"
            "Limitations:\n"
            "- This review is static and does not validate runtime behaviour, integration execution, "
            "or QA outcomes.\n\n"
            "Findings:\n"
            "- No actionable developer findings were identified from the diff."
        )

    blocks = ["PR Review Findings:"]

    for comment in comments:
        blocks.append(
            (
                f"\nFile: {comment.file}:{comment.line}\n"
                f"Severity: {comment.severity}\n"
                f"Category: {comment.category}\n\n"
                f"Observation:\n"
                f"- {comment.message}\n\n"
                f"Impact:\n"
                f"- {comment.rationale}\n\n"
                f"Suggestion:\n"
                f"- Address this before progressing the PR, or update the ticket if the intended behaviour has changed."
            )
        )

    return "\n".join(blocks)


def _format_jira_comment(analysis: LLMReviewOutput) -> str:
    blocking_findings = [
        comment
        for comment in analysis.pr_comments
        if (
                comment.severity == "high"
                or comment.category in {"consistency", "validation"}
                or (
                        comment.category == "risk"
                        and comment.severity in {"medium", "high"}
                )
        )
    ]

    if blocking_findings:
        blocks = [
            "Reviewed the PR against the ticket.",
            "",
            "Acceptance criteria / ticket alignment concerns:",
        ]

        for finding in blocking_findings:
            blocks.append(f"- {finding.message}")

        blocks.extend(
            [
                "",
                "Observed:",
            ]
        )

        for finding in blocking_findings:
            blocks.append(f"- {finding.rationale}")

        blocks.extend(
            [
                "",
                "Outcome:",
                "- Potential acceptance criteria or ticket intent mismatch identified.",
                "",
                "QA Action:",
            ]
        )

        if analysis.qa_checklist:
            for item in analysis.qa_checklist:
                blocks.append(f"- {item.title}")
                for step in item.steps:
                    blocks.append(f"  - {step}")
                blocks.append(f"  Expected result: {item.expected_result}")
        else:
            blocks.extend(
                [
                    "- Validate the affected behaviour against the acceptance criteria.",
                    "- Block progression if expected behaviour is not present.",
                    "- Sync with the developer if implementation intent is unclear.",
                ]
            )

        return "\n".join(blocks)

    return _format_qa_checklist(analysis.qa_checklist)


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


def _format_jira_comment(analysis: LLMReviewOutput) -> str:
    blocking_findings = [
        comment
        for comment in analysis.pr_comments
        if (
                comment.severity == "high"
                or comment.category in {"consistency", "validation"}
                or (
                        comment.category == "risk"
                        and comment.severity in {"medium", "high"}
                )
        )
    ]

    if blocking_findings:
        blocks = [
            "Reviewed the PR against the ticket.",
            "",
            "Acceptance criteria / ticket alignment concerns:",
        ]

        for finding in blocking_findings:
            blocks.append(f"- {finding.message}")

        blocks.extend(
            [
                "",
                "Observed:",
            ]
        )

        for finding in blocking_findings:
            blocks.append(f"- {finding.rationale}")

        blocks.extend(
            [
                "",
                "Outcome:",
                "- Potential acceptance criteria or ticket intent mismatch identified.",
                "",
                "QA Action:",
            ]
        )

        if analysis.qa_checklist:
            for item in analysis.qa_checklist:
                blocks.append(f"- {item.title}")
                for step in item.steps:
                    blocks.append(f"  - {step}")
                blocks.append(f"  Expected result: {item.expected_result}")
        else:
            blocks.extend(
                [
                    "- Validate the affected behaviour against the acceptance criteria.",
                    "- Block progression if expected behaviour is not present.",
                    "- Sync with the developer if implementation intent is unclear.",
                ]
            )

        return "\n".join(blocks)

    return _format_qa_checklist(analysis.qa_checklist)

