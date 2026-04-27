# PRClosure

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-webhook%20service-009688) ![OpenWebUI](https://img.shields.io/badge/LLM-OpenWebUI%20local-6f42c1) ![Tests](https://img.shields.io/badge/tests-pytest-brightgreen) ![Status](https://img.shields.io/badge/status-working%20reference%20implementation-blue) ![License](https://img.shields.io/badge/license-internal%20%2F%20personal-lightgrey)

PRClosure is a FastAPI webhook service that connects GitHub, Jira, and a local LLM through OpenWebUI to review pull requests against ticket intent and acceptance criteria.

It is built for the handover point between development and quality: helping developers and QA share clearer context, surface risk earlier, and reduce the "does this actually meet the ticket?" loop.

## Why PRClosure exists

PRClosure is built around a simple leadership belief:

> People do their best work when they understand the purpose, not just the task.

Happy teams move faster, catch more, and care about the outcome. Worn-out teams just ship and survive.

Strong teams keep context moving with the work. Developers, quality engineers, product people, and delivery leads all need the same thread of meaning if they are going to move toward the same definition of done.

A pull request can be marked as done, but QA still has to answer the harder question:

> Does this change actually match the ticket intent and acceptance criteria?

That question should not live only in someone’s head.

PRClosure is a small experiment in tightening that space.

It gathers the pull request diff and the related Jira ticket context, then asks a local LLM to review the work against that context.

The review must pass a strict output contract before anything is written back to GitHub or Jira.

If the output is invalid, it blocks.

That boundary matters.

PRClosure stays advisory. It gives the team a structured second read before QA begins, so risk is easier to see and context is easier to share.

Good delivery keeps meaning intact as the work moves.

For me, the point is simple:

> Context should move with the work.

## What PRClosure does

- Receives GitHub pull request webhook events
- Validates the GitHub webhook signature
- Returns `202 Accepted` quickly
- Processes the review in the background
- Extracts the ticket key from the branch name or PR title
- Fetches Jira ticket context
- Fetches the GitHub PR diff
- Sends deterministic review context to OpenWebUI
- Requires structured JSON output from the LLM
- Validates the output before write-back
- Writes developer-facing feedback to GitHub
- Writes QA-facing handover guidance to Jira
- Uses marker-based upsert comments to avoid duplicate write-back noise

## What PRClosure does not do

PRClosure is advisory only.

It does not:

- approve pull requests
- merge code
- close Jira tickets
- mark QA as passed
- replace developer review
- replace QA validation
- prove runtime behaviour correct

Clean output means:

```text
No actionable developer findings were identified from the diff.
```

It does not mean:

```text
The change is proven correct.
```

Runtime behaviour remains QA-owned.

## Who this is for

PRClosure is useful for teams that want a controlled AI-assisted review handover between development and quality.

It is designed for:

- engineering teams using GitHub pull requests
- teams using Jira tickets with acceptance criteria or detailed descriptions
- local-first LLM workflows through OpenWebUI
- environments where AI output must be bounded, validated, and advisory
- teams that want fewer vague QA handovers and more explicit validation context

It is not currently packaged as a GitHub Action, hosted SaaS product, or public bot.

## Quick start

Clone the repository:

```bash
git clone https://github.com/OLO-Governor/olo-pr-closure.git
cd olo-pr-closure
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS or Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```bash
copy .env.example .env
```

Run the service:

```bash
uvicorn main:app --host 0.0.0.0 --port 8765
```

Webhook endpoint:

```text
POST /webhook/github
```

## Requirements

- Python 3.10+
- GitHub repository with webhook access
- Jira account with API access
- OpenWebUI running locally or accessible over HTTP
- A local or hosted model available through OpenWebUI
- A reachable webhook URL for GitHub delivery

For local webhook testing, expose the service through a tunnel or reverse proxy, then point the GitHub webhook at:

```text
https://<your-domain>/webhook/github
```

## Environment variables

Create a `.env` file based on `.env.example`.

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
OPENWEBUI_MODEL=qwen3:30b-a3b

PRCLOSURE_PROMPT_FILE=
```

| Variable | Required | Purpose |
|---|---:|---|
| `GITHUB_TOKEN` | Yes | GitHub API token used to fetch PR diffs and write PR comments |
| `GITHUB_WEBHOOK_SECRET` | Yes | Secret used to verify GitHub webhook signatures |
| `JIRA_BASE_URL` | Yes | Base URL for the Jira instance |
| `JIRA_EMAIL` | Yes | Jira account email used for API access |
| `JIRA_API_TOKEN` | Yes | Jira API token |
| `JIRA_API_VERSION` | No | Jira API version, defaults to `3` |
| `JIRA_ACCEPTANCE_CRITERIA_FIELD` | No | Optional custom Jira field for acceptance criteria |
| `OPENWEBUI_URL` | Yes | OpenWebUI API URL |
| `OPENWEBUI_API_KEY` | Yes | OpenWebUI API key |
| `OPENWEBUI_MODEL` | Yes | Model name to use through OpenWebUI |
| `PRCLOSURE_PROMPT_FILE` | No | Optional override path for the system prompt |

If `JIRA_ACCEPTANCE_CRITERIA_FIELD` is empty or returns no value, PRClosure instructs the LLM to extract acceptance criteria from the Jira ticket description.

If `PRCLOSURE_PROMPT_FILE` is not set, the default prompt is loaded from:

```text
prompts/pr_review_system_prompt.txt
```

## GitHub webhook setup

Configure a webhook on the target repository.

| Setting | Value |
|---|---|
| Payload URL | `https://<your-domain>/webhook/github` |
| Content type | `application/json` |
| Secret | Must match `GITHUB_WEBHOOK_SECRET` |
| Events | Pull request |

Required behaviour:

- GitHub sends a pull request event
- PRClosure validates `X-Hub-Signature-256`
- Invalid signatures are rejected
- Valid PR events receive `202 Accepted`
- Processing continues in the background

## OpenWebUI setup

OpenWebUI must be reachable from PRClosure through `OPENWEBUI_URL`.

PRClosure expects the model to:

- follow the system prompt
- return JSON only
- avoid Markdown wrappers
- avoid inventing ticket context
- report uncertainty instead of fabricating findings
- stay inside the advisory role boundary

The prompt can be changed by setting:

```env
PRCLOSURE_PROMPT_FILE=path/to/custom_prompt.txt
```

## Example review flow

```text
GitHub PR Event
  -> FastAPI /webhook/github
  -> Validate GitHub webhook signature
  -> Return 202 Accepted
  -> Process PR in background
  -> Extract ticket key from branch or PR title
  -> Fetch Jira ticket context
  -> Fetch PR diff from GitHub
  -> Build unified context payload
  -> Send context to OpenWebUI
  -> Receive structured JSON output
  -> Validate strict output contract
  -> Block write-back if output is invalid
  -> Upsert GitHub developer-facing comment
  -> Upsert Jira QA-facing handover comment
```

## Example output

### GitHub developer-facing comment

```markdown
AI-assisted diff review completed.

Scope:

Code changes in the PR diff were reviewed against ticket intent and acceptance criteria where visible.

Limitations:

This review is static and does not validate runtime behaviour, integration execution, or QA outcomes.

Findings:

No actionable developer findings were identified from the diff.
```

### Jira QA-facing comment

```markdown
<!-- prclosure:OPRC-19 -->

Reviewed the PR against the ticket.

Validated:
- Acceptance criteria were checked against the changes where possible from the diff.

Observed:
- No specific risks or edge cases were identified from the changes.

Outcome:
- No gaps identified from code review. Behaviour should be confirmed in QA.

QA Action:
- Verify acceptance criteria are met in a running environment.
- Confirm no regression in related behaviour.
```

## LLM output contract

The LLM must return a JSON object with exactly two top-level keys:

```json
{
  "pr_comments": [],
  "qa_checklist": []
}
```

Unknown top-level keys are rejected.

### `pr_comments`

Each PR comment must use this shape:

```json
{
  "file": "application/example.py",
  "line": 42,
  "severity": "medium",
  "category": "validation",
  "message": "The implementation appears to miss an acceptance criteria path.",
  "rationale": "The Jira ticket describes this behaviour, but the diff does not show matching handling."
}
```

| Field | Type | Rule |
|---|---|---|
| `file` | string | Required, non-empty |
| `line` | integer | Required, must be greater than `0` |
| `severity` | string | `low`, `medium`, or `high` |
| `category` | string | `risk`, `validation`, or `consistency` |
| `message` | string | Required, max 240 characters |
| `rationale` | string | Required, max 500 characters |

### `qa_checklist`

Each QA checklist item must use this shape:

```json
{
  "title": "Validate acceptance criteria coverage",
  "steps": [
    "Open the affected workflow.",
    "Run through the ticket acceptance criteria.",
    "Confirm the expected result is visible in the running system."
  ],
  "acceptance_criteria_ref": "Acceptance criteria from Jira ticket description",
  "expected_result": "The implemented behaviour matches the ticket intent without regression."
}
```

| Field | Type | Rule |
|---|---|---|
| `title` | string | Required, max 160 characters |
| `steps` | array of strings | Required, non-empty, each step max 240 characters |
| `acceptance_criteria_ref` | string | Required, max 160 characters |
| `expected_result` | string | Required, max 240 characters |

### Invalid output is blocked

The validator rejects:

- non-JSON output
- missing top-level keys
- unknown top-level keys
- invalid PR comment shape
- invalid QA checklist shape
- invalid severity values
- invalid category values
- empty required fields
- excessive field length

No invalid LLM output is written to GitHub or Jira.

## Write-back model

PRClosure uses a converging upsert model.

Each run updates existing comments instead of creating duplicate comments.

Marker:

```html
<!-- prclosure:{ticket_key} -->
```

Write-back surfaces:

| Surface | Audience | Purpose |
|---|---|---|
| GitHub PR comment | Developers | Code-level findings, validation risks, implementation concerns |
| Jira comment | QA | Ticket alignment, acceptance criteria guidance, QA validation actions |

GitHub comments are intended for developer-facing findings.

Jira comments are intended for QA-facing handover and validation guidance.

## Failure handling

PRClosure enforces strict boundaries.

| Condition | Behaviour |
|---|---|
| Missing ticket key | Processing blocked |
| Ticket not found | Processing blocked |
| Empty diff | Processing skipped |
| Invalid webhook signature | Request rejected with `401` |
| LLM unavailable | No write-back |
| Invalid LLM output | No write-back |
| GitHub write-back failure | Jira write-back is not attempted |
| Jira write-back failure | Processing raises a write-back failure |

## Guardrails

This project is intended for controlled environments.

For production or public use:

- enforce authentication around exposed endpoints
- keep webhook signature validation enabled
- store secrets securely
- do not commit `.env` files
- validate all LLM output before write-back
- use least-privilege GitHub and Jira credentials
- implement rate limiting if exposed beyond a private environment
- keep AI advisory only
- do not automate merge, approval, QA pass, or ticket closure authority

## Testing

Run the test suite:

```bash
pytest
```

The test suite covers:

- webhook route behaviour
- GitHub signature validation
- ticket key parsing
- OpenWebUI client behaviour
- output contract validation
- background processing
- fetch and write-back contracts
- GitHub and Jira write-back behaviour

## Project structure

```text
.
├── main.py
├── README.md
├── requirements.txt
├── test_main.http
├── application/
│   ├── background_tasks.py
│   ├── webhook_fetch.py
│   └── webhook_put.py
├── domain/
│   ├── models.py
│   ├── output_contract.py
│   └── services.py
├── infrastructure/
│   ├── config.py
│   ├── github_client.py
│   ├── jira_client.py
│   └── openwebui_client.py
├── presentation/
│   ├── routes.py
│   └── middleware/
│       └── github_signature.py
├── prompts/
│   └── pr_review_system_prompt.txt
└── tests/
    ├── conftest.py
    ├── test_background_tasks.py
    ├── test_context.py
    ├── test_openwebui_client.py
    ├── test_output_contract.py
    ├── test_parser.py
    ├── test_routes.py
    ├── test_ticket.py
    ├── test_webhook_fetch_contract.py
    └── test_writeback.py
```

### Key areas

| Area | Purpose |
|---|---|
| `main.py` | FastAPI application entry point |
| `application/` | Orchestration layer for webhook processing, background execution, fetch, and write-back |
| `domain/` | Core models, parsing, validation, and service logic |
| `infrastructure/` | External system clients and runtime configuration |
| `presentation/` | HTTP routes and request validation middleware |
| `prompts/` | Default LLM review prompt |
| `tests/` | Unit and contract tests for routing, parsing, validation, clients, and write-back behaviour |

## Suggested GitHub repository description

Use this as the repository About description:

```text
FastAPI service that reviews GitHub PRs against Jira ticket context using a local OpenWebUI LLM, then writes bounded developer and QA handover feedback.
```

Suggested topics:

```text
fastapi github jira openwebui llm qa pull-request-review ai-assisted-review webhook
```

## Status

PRClosure is a working reference implementation of bounded AI-assisted engineering workflow orchestration.

It focuses on:

- control
- validation
- convergence
- local-first LLM use
- developer and QA alignment

## License

No public license has been published yet.

Until a license is added, this should be treated as an internal / personal project.
