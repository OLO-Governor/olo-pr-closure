from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from starlette.status import HTTP_202_ACCEPTED

from application.background_tasks import process_webhook

router = APIRouter()


@router.post("/webhook/github", status_code=HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    pr = payload.get("pull_request")
    if not pr:
        raise HTTPException(status_code=400, detail="Not a PR event")

    background_tasks.add_task(process_webhook, payload)

    return {
        "status": "accepted",
        "message": "Webhook accepted for background processing",
    }
