# application/webhook_fetch.py

import domain.services
from infrastructure.jira_client import jira_client
from infrastructure.github_client import github_client
from infrastructure.openwebui_client import openwebui_client


def handle_webhook(payload):
    pr = payload.get("pull_request")
    if not pr:
        return None, "Not a PR event"

    branch = pr.get("head", {}).get("ref", "")
    title = pr.get("title", "")
    pr_id = pr.get("id")

    ticket_key = domain.services.extract_ticket_key(branch, title)
    if not ticket_key:
        return None, "Missing ticket key"

    ticket = domain.services.fetch_ticket(jira_client, ticket_key)
    if not ticket:
        return None, "Ticket not found"

    repo_info = domain.services.extract_repo_info(payload)
    pr_number = domain.services.extract_pr_number(pr)

    diff = domain.services.fetch_pr_diff(
        github_client,
        repo_info["owner"],
        repo_info["repo"],
        pr_number
    )

    if not diff:
        return None, "Empty diff"

    context = domain.services.build_context(
        {
            "id": pr_id,
            "branch": branch,
            "title": title,
            "diff": diff,
            "repo_owner": repo_info["owner"],
            "repo_name": repo_info["repo"],
            "number": pr_number
        },
        ticket
    )

    analysis = openwebui_client.analyze(context)
    if not analysis:
        return context, "LLM unavailable"

    content = analysis["choices"][0]["message"]["content"] if analysis else None

    parsed = domain.services.parse_llm_output(content)

    from application.webhook_put import handle_writeback

    try:
        handle_writeback(
            github_client,
            jira_client,
            context,
            parsed
        )
    except Exception as e:
        print("WRITEBACK ERROR:", str(e))
        return None, "Write-back failed"

    return {
        "context": context,
        "analysis": parsed
    }, None
