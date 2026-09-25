# ============================================================
# app/main.py — Webhook server entry point (FastAPI)
# ============================================================
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

from app.config import settings
from app.webhooks.github_webhook import handle_github_event
from app.webhooks.gitlab_webhook import handle_gitlab_event

app = FastAPI(title="AI Code Reviewer")


def verify_github_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return False
    expected = "sha256=" + hmac.new(
        settings.WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@app.post("/webhooks/github")
async def github_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if not verify_github_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    data = await request.json()

    result = await handle_github_event(event_type, data)
    return {"status": "ok", "result": result}


@app.post("/webhooks/gitlab")
async def gitlab_webhook(request: Request):
    token = request.headers.get("X-Gitlab-Token", "")
    if token != settings.GITLAB_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")

    data = await request.json()
    result = await handle_gitlab_event(data)
    return {"status": "ok", "result": result}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)