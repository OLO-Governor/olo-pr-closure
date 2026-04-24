from domain.models import PullRequest
import json
import re


def build_context(pr_data, ticket_data):
    pr = PullRequest(
        pr_id=pr_data["id"],
        branch=pr_data["branch"],
        title=pr_data["title"]
    )

    return {
        "pr": {
            **vars(pr),
            "diff": pr_data.get("diff"),
            "repo_owner": pr_data.get("repo_owner"),
            "repo_name": pr_data.get("repo_name"),
            "number": pr_data.get("number")
        },
        "ticket": ticket_data
    }


TICKET_PATTERN = re.compile(r"[A-Z]+-\d+")


def extract_ticket_key(branch, title):
    match = TICKET_PATTERN.search(branch) or TICKET_PATTERN.search(title)
    return match.group(0) if match else None


def fetch_ticket(jira_client, ticket_key):
    return jira_client.get_ticket(ticket_key)


def extract_repo_info(payload):
    repo_data = payload.get("repository", {})

    return {
        "owner": repo_data.get("owner", {}).get("login"),
        "repo": repo_data.get("name")
    }


def extract_pr_number(pr):
    return pr.get("number")


def fetch_pr_diff(github_client, owner, repo, pr_number):
    return github_client.get_pr_diff(owner, repo, pr_number)


def parse_llm_output(raw_content: str):
    if not raw_content:
        return None

    # strip ```json ... ```
    match = re.search(r"```json\s*(\{.*\})\s*```", raw_content, re.DOTALL)
    if match:
        raw_content = match.group(1)

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        return None
