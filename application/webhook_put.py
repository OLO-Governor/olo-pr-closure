def handle_writeback(github_client, jira_client, context, analysis):
    pr = context["pr"]
    ticket = context["ticket"]

    comments = analysis.get("comments", [])
    checklist = analysis.get("checklist", [])

    repo_owner = pr.get("repo_owner")
    repo_name = pr.get("repo_name")
    pr_number = pr.get("number")

    marker = f"<!-- prclosure:{ticket['key']} -->"

    # Upsert PR comment: updates existing comment (by marker) or creates new
    try:
        github_client.upsert_structured_pr_comment(
            repo_owner,
            repo_name,
            pr_number,
            comments,
            marker
        )
    except Exception as e:
        # log and continue without breaking entire flow
        print("GITHUB WRITE ERROR:", str(e))

    try:
        jira_client.upsert_structured_comment(
            ticket["key"],
            checklist,
            marker
        )
    except Exception as e:
        print("JIRA WRITE ERROR:", str(e))
