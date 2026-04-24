def handle_writeback(github_client, jira_client, context, analysis):
    pr = context["pr"]
    ticket = context["ticket"]

    comments = analysis.get("comments", [])
    checklist = analysis.get("checklist", [])

    gh_body = "\n".join([
        f"- {c['file']}:{c['line']} → {c['comment']}"
        for c in comments
    ])

    jira_body = "\n".join([
        f"- [ ] {item['item']}"
        for item in checklist
    ])

    repo_owner = pr.get("repo_owner")
    repo_name = pr.get("repo_name")
    pr_number = pr.get("number")

    marker = f"<!-- prclosure:{ticket['key']} -->"

    # Upsert PR comment: updates existing comment (by marker) or creates new
    github_client.upsert_pr_comment(
        repo_owner,
        repo_name,
        pr_number,
        gh_body,
        marker
    )

    jira_client.add_comment_if_new(
        ticket["key"],
        jira_body,
        marker
    )
