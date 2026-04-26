import logging
import requests

import domain.services
from application.webhook_put import handle_writeback
from domain.output_contract import validate_llm_output
from infrastructure.github_client import github_client
from infrastructure.jira_client import jira_client
from infrastructure.openwebui_client import openwebui_client

logger = logging.getLogger(__name__)


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
        pr_number,
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
            "number": pr_number,
        },
        ticket,
    )

    analysis = openwebui_client.analyze(context)
    if not analysis:
        return context, "LLM unavailable"

    content = _extract_llm_content(analysis)

    logger.warning("PRClosure raw LLM content:\n%s", content)

    validation = validate_llm_output(content)
    if not validation.valid or validation.output is None:
        return {
            "context": context,
            "validation_errors": validation.errors,
            "raw_llm_output": content,
        }, "Invalid LLM output"

    logger.warning("PRClosure parsed LLM output:\n%s", validation.output)

    try:
        handle_writeback(
            github_client,
            jira_client,
            context,
            validation.output,
        )
    except (requests.RequestException, KeyError, TypeError, AttributeError) as e:
        return {
            "context": context,
            "analysis": validation.output,
            "error": str(e),
        }, "Write-back failed"

    return {
        "context": context,
        "analysis": validation.output,
    }, None


def _extract_llm_content(analysis):
    try:
        return analysis["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None
