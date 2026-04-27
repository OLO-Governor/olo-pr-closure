# PR Closure Bridge Service

A FastAPI-based orchestration service that connects GitHub, Jira, and a local LLM (OpenWebUI) to automate pull request review and QA preparation.

---

## Overview

This service listens to GitHub pull request events, enriches them with Jira ticket context, sends a unified payload to a local LLM, and writes structured outputs back to GitHub and Jira.

It is designed as a **reference implementation** of a controlled AI-assisted engineering workflow.

---

## Flow

```text
GitHub PR Event
  → FastAPI /webhook/github
  → Validate GitHub webhook signature
  → Return 202 Accepted
  → Process PR in background
  → Extract ticket key from branch or PR title
  → Fetch Jira ticket context
       - summary
       - description
       - acceptance criteria field when configured
  → Fetch PR diff from GitHub
  → Build unified context payload
  → Send deterministic context to OpenWebUI
  → LLM extracts acceptance criteria
       - from ticket.acceptance_criteria when present
       - from ticket.description when acceptance_criteria is empty
  → Receive structured JSON output
  → Validate strict output contract
  → Block write-back if output is invalid
  → Write-back using marker-based upsert:
       - GitHub → developer-facing PR review comment
       - Jira → QA-facing review handover / validation guidance
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

```env
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=

JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_API_VERSION=3
JIRA_ACCEPTANCE_CRITERIA_FIELD=

OPENWEBUI_URL=
OPENWEBUI_API_KEY=
OPENWEBUI_MODEL=

PRCLOSURE_PROMPT_FILE=
```

Notes:

``JIRA_ACCEPTANCE_CRITERIA_FIELD`` is optional.
If ``JIRA_ACCEPTANCE_CRITERIA_FIELD`` is empty or returns no value, the LLM is instructed to extract acceptance
criteria from the Jira description.
``PRCLOSURE_PROMPT_FILE`` is optional.
If ``PRCLOSURE_PROMPT_FILE`` is not set, the default prompt is loaded from: ``prompts/pr_review_system_prompt.txt``

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

The system uses a converging upsert model.

Each run updates existing comments instead of creating duplicates.

Marker used:

```
<!-- prclosure:{ticket_key} -->
```

Write-back surfaces:

GitHub:

- Developer-facing PR review comment

Jira:

- QA-facing review handover comment

GitHub comments are intended for developers and may include:

* file and line
* severity
* category
* observation
* impact
* suggestion

Jira comments are intended for QA and may include:

* reviewed ticket context
* acceptance criteria / ticket alignment concerns
* observed review findings
* outcome
* QA action

Jira can surface blocking PR findings when they affect ticket intent, acceptance criteria, validation, or behavioural risk.

---

## Failure Handling

The system enforces strict boundaries:

- Missing ticket key → processing blocked
- Ticket not found → processing blocked
- Empty diff → processing skipped
- Invalid webhook signature → rejected with 401
- LLM unavailable → no write-back
- Invalid LLM output → no write-back
- GitHub write-back failure → Jira write-back is not attempted
- Jira write-back failure → processing raises a write-back failure

No invalid LLM output is written to GitHub or Jira.

## LLM Output Contract

The LLM must return JSON only.

Expected top-level shape:

```json
{
  "pr_comments": [],
  "qa_checklist": []
}
```

Invalid output is blocked before write-back.

The validator rejects:

* non-JSON output
* missing top-level keys
* unknown top-level keys
* invalid PR comment shape
* invalid QA checklist shape
* invalid severity values
* invalid category values
* excessive field length

The LLM is advisory only.

It has no authority to:

* approve a pull request
* merge a pull request
* close a Jira ticket
* mark QA as passed

---

## Role Boundaries

PRClosure separates output by audience.

```text
GitHub = developer-facing
Jira   = QA-facing
```

GitHub should contain:

* code-level review findings
* implementation risks
* validation issues
* ticket or acceptance-criteria mismatches
* developer-facing suggestions

Jira should contain:

* QA validation guidance
* acceptance criteria concerns
* behavioural risks requiring QA attention
* clear QA action

PRClosure must not imply that QA can be skipped.

Clean review output means: ``No actionable developer findings were identified from the diff.``
It does not mean: ``The change is proven correct.``

Runtime behaviour remains QA-owned.

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
