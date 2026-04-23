from fastapi import FastAPI, Request, HTTPException
import re

app = FastAPI()

TICKET_PATTERN = re.compile(r"[A-Z]+-\d+")


# Extract
def extract_ticket_key(text: str):
    match = TICKET_PATTERN.search(text or "")
    return match.group(0) if match else None


@app.post("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.json()

    pr = payload.get("pull_request")
    if not pr:
        raise HTTPException(status_code=400, detail="Not a PR event")

    pr_id = pr.get("id")
    branch = pr.get("head", {}).get("ref", "")
    title = pr.get("title", "")

    ticket_key = extract_ticket_key(branch) or extract_ticket_key(title)

    if not ticket_key:
        raise HTTPException(status_code=400, detail="Missing ticket key")

    return {
        "pr_id": pr_id,
        "branch": branch,
        "title": title,
        "ticket_key": ticket_key
    }
