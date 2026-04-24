from fastapi import APIRouter, Request, HTTPException
from application.webhook_fetch import handle_webhook

router = APIRouter()


@router.post("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.json()

    result, error = handle_webhook(payload)

    if error == "Not a PR event":
        raise HTTPException(status_code=400, detail=error)

    if error == "Missing ticket key":
        raise HTTPException(status_code=400, detail=error)

    if error == "Ticket not found":
        raise HTTPException(status_code=404, detail=error)

    return result
