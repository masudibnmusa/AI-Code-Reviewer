# ============================================================
# app/review_engine/llm.py — Claude API wrapper
# ============================================================
import json
import httpx

from app.config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


async def call_llm(prompt: str) -> str:
    headers = {
        "x-api-key": settings.LLM_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(ANTHROPIC_API_URL, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    return "\n".join(text_blocks)


def parse_json_findings(raw_text: str) -> list:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return []