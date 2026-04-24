import hmac
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from infrastructure.config import config


class GitHubSignatureMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path != "/webhook/github":
            return await call_next(request)

        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")

        if not signature or not self._is_valid(body, signature):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid signature"}
            )

        return await call_next(request)

    @staticmethod
    def _is_valid(body: bytes, signature: str) -> bool:
        secret = config.GITHUB_WEBHOOK_SECRET

        if not secret:
            return False

        expected = "sha256=" + hmac.new(
            secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
