import hmac
import hashlib
import json

from fastapi.testclient import TestClient

from main import app
from infrastructure.config import config


client = TestClient(app)


def _signature(body: bytes) -> str:
    return "sha256=" + hmac.new(
        config.GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()


def test_valid_pr_webhook_returns_202(monkeypatch):
    calls = []

    def fake_process_webhook(received_payload):
        calls.append(received_payload)

    monkeypatch.setattr(
        "presentation.routes.process_webhook",
        fake_process_webhook,
    )

    payload = {
        "pull_request": {
            "id": 1,
            "number": 12,
            "title": "OPRC-12 async webhook",
            "head": {
                "ref": "OPRC-12-async-webhook",
            },
        },
        "repository": {
            "name": "olo-pr-closure",
            "owner": {
                "login": "OLO-Governor",
            },
        },
    }

    body = json.dumps(payload).encode()

    response = client.post(
        "/webhook/github",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _signature(body),
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    assert calls == [payload]


def test_invalid_json_returns_400():
    body = b"{not-json"

    response = client.post(
        "/webhook/github",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _signature(body),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON payload"


def test_non_pr_event_returns_400():
    payload = {
        "zen": "Keep it logically awesome.",
    }

    body = json.dumps(payload).encode()

    response = client.post(
        "/webhook/github",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": _signature(body),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Not a PR event"


def test_missing_signature_returns_401():
    payload = {
        "pull_request": {
            "id": 1,
        },
    }

    response = client.post(
        "/webhook/github",
        json=payload,
    )

    assert response.status_code == 401


def test_invalid_signature_returns_401():
    payload = {
        "pull_request": {
            "id": 1,
        },
    }

    response = client.post(
        "/webhook/github",
        json=payload,
        headers={
            "X-Hub-Signature-256": "sha256=invalid",
        },
    )

    assert response.status_code == 401
