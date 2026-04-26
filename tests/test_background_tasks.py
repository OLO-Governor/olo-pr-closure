import logging

from application.background_tasks import process_webhook


def test_process_webhook_logs_success(monkeypatch, caplog):
    def fake_handle_webhook(_payload):
        return {"ok": True}, None

    monkeypatch.setattr(
        "application.background_tasks.handle_webhook",
        fake_handle_webhook,
    )

    with caplog.at_level(logging.INFO):
        result = process_webhook({"pull_request": {"id": 1}})

    assert result == {"ok": True}
    assert "completed successfully" in caplog.text


def test_process_webhook_logs_known_error(monkeypatch, caplog):
    def fake_handle_webhook(_payload):
        return None, "Missing ticket key"

    monkeypatch.setattr(
        "application.background_tasks.handle_webhook",
        fake_handle_webhook,
    )

    with caplog.at_level(logging.WARNING):
        result = process_webhook({"pull_request": {"id": 1}})

    assert result is None
    assert "completed with error: Missing ticket key" in caplog.text


def test_process_webhook_logs_exception(monkeypatch, caplog):
    def fake_handle_webhook(_payload):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "application.background_tasks.handle_webhook",
        fake_handle_webhook,
    )

    with caplog.at_level(logging.ERROR):
        result = process_webhook({"pull_request": {"id": 1}})

    assert result is None
    assert "background processing failed" in caplog.text
    assert "RuntimeError: boom" in caplog.text
