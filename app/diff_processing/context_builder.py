# ============================================================
# app/diff_processing/context_builder.py — Fetch surrounding code
# ============================================================
import httpx
import base64

from app.config import settings
from app.diff_processing.diff_fetcher import ChangedFile, GITHUB_API, GITLAB_API


async def build_context(repo_or_project, file: ChangedFile, provider: str) -> str:
    """
    Fetch the full current file content so the LLM has more than
    just the diff hunk to reason about (imports, surrounding
    functions, class definitions, etc).
    """
    if file.status == "removed":
        return ""

    if provider == "github":
        return await _fetch_github_file(repo_or_project, file.path)
    elif provider == "gitlab":
        return await _fetch_gitlab_file(repo_or_project, file.path)
    raise ValueError(f"Unknown provider: {provider}")


async def _fetch_github_file(repo_full_name: str, path: str) -> str:
    url = f"{GITHUB_API}/repos/{repo_full_name}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data.get("content", "")


async def _fetch_gitlab_file(project_id, path: str) -> str:
    from urllib.parse import quote
    encoded_path = quote(path, safe="")
    url = f"{GITLAB_API}/projects/{project_id}/repository/files/{encoded_path}/raw"
    headers = {"PRIVATE-TOKEN": settings.GITLAB_TOKEN}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params={"ref": "HEAD"})
        if resp.status_code != 200:
            return ""
        return resp.text