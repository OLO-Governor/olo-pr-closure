# PR Closure Bridge Service

A FastAPI-based orchestration service that connects GitHub, Jira, and a local LLM (OpenWebUI) to automate pull request review and QA preparation.

---

## Overview

This service listens to GitHub pull request events, enriches them with Jira ticket context, sends a unified payload to a local LLM, and writes structured outputs back to GitHub and Jira.

It is designed as a **reference implementation** of a controlled AI-assisted engineering workflow.

---

## Flow

```
GitHub PR Event
  → FastAPI /webhook/github
  → Extract ticket key (branch or title)
  → Fetch Jira ticket (description, acceptance criteria)
  → Fetch PR diff (GitHub API)
  → Build unified context payload
  → Send to OpenWebUI (LLM)
  → Receive structured output
  → Parse output (comments + checklist)
  → Write-back (upsert):
       PR comments → GitHub (single evolving comment)
       QA checklist → Jira (draft, updated in place)
```

---

## Features

- End-to-end orchestration across GitHub, Jira, and LLM
- Structured PR review comments (high-signal, diff-aware)
- QA checklist generation mapped to ticket intent
- Upsert-based write-back (no duplicate comments, converging output)
- Explicit failure boundaries (safe execution)
- Local-first LLM integration (OpenWebUI)
- Webhook signature validation (HMAC SHA256)

---

## Project Structure

```
application/
  webhook_fetch.py
  webhook_put.py

domain/
  models.py
  services.py

infrastructure/
  config.py
  github_client.py
  jira_client.py
  openwebui_client.py

presentation/
  routes.py
  middleware/github_signature.py

tests/

main.py
```

---

## Requirements

- Python 3.10+
- GitHub repository with webhook access
- Jira account with API access
- OpenWebUI running locally or accessible via HTTP

---

## Environment Variables

Create a `.env` file based on:

```
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=

JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=

OPENWEBUI_URL=
OPENWEBUI_API_KEY=
OPENWEBUI_MODEL=
```

---

## Installation

```
python -m venv venv
venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

---

## Running the Service

```
uvicorn main:app --host 0.0.0.0 --port 8765
```

Endpoint:

```
POST /webhook/github
```

---

## GitHub Webhook Setup

Configure a webhook on your repository:

- URL: `https://<your-domain>/webhook/github`
- Method: `POST`
- Content type: `application/json`
- Secret: must match `GITHUB_WEBHOOK_SECRET`
- Events:
  - Pull request

---

## OpenWebUI

- Must be running and accessible via `OPENWEBUI_URL`
- Used for LLM inference only
- Expected to return structured JSON output

---

## Writeback Model

The system uses a **converging upsert model**:

- One comment per PR
- One checklist per Jira ticket
- Each run updates existing outputs instead of creating new ones

Marker used:

```
<!-- prclosure:{ticket_key} -->
```

---

## Failure Handling

The system enforces strict boundaries:

- Missing ticket key → processing blocked
- Ticket not found → blocked
- Empty diff → skipped
- Invalid webhook signature → rejected (401)
- API failure → no write-back
- LLM unavailable → no output

No partial or unsafe writes occur.

---

## Guardrails

This project is intended for controlled environments.

For production or public use:

- Enforce authentication on all endpoints
- Store secrets securely (never in source)
- Validate all LLM outputs before write-back
- Implement rate limiting and retries
- Respect GitHub and Jira permission models
- Do not automate merges or ticket closure

---

## Notes

- This is a working system, not a mock or prototype
- It demonstrates orchestration and bounded AI execution
- Focus is on control, convergence, and integration patterns

---

## License

Internal / personal project