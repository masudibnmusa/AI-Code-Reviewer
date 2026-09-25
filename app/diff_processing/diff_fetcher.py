# ============================================================
# app/diff_processing/diff_fetcher.py — Pull changed files + diffs
# ============================================================
import httpx
from dataclasses import dataclass
from typing import List

from app.config import settings


@dataclass
class ChangedFile:
    path: str
    status: str          # added | modified | removed | renamed
    patch: str            # unified diff text
    additions: int
    deletions: int


GITHUB_API = "https://api.github.com"
GITLAB_API = "https://gitlab.com/api/v4"


async def fetch_pr_diff(repo_or_project, pr_or_mr_number, provider: str) -> List[ChangedFile]:
    if provider == "github":
        return await _fetch_github_diff(repo_or_project, pr_or_mr_number)
    elif provider == "gitlab":
        return await _fetch_gitlab_diff(repo_or_project, pr_or_mr_number)
    raise ValueError(f"Unknown provider: {provider}")


async def _fetch_github_diff(repo_full_name: str, pr_number: int) -> List[ChangedFile]:
    url = f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    files = []
    async with httpx.AsyncClient() as client:
        page = 1
        while True:
            resp = await client.get(url, headers=headers, params={"per_page": 100, "page": page})
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break

            for f in batch:
                if _should_skip(f["filename"]):
                    continue
                files.append(ChangedFile(
                    path=f["filename"],
                    status=f["status"],
                    patch=f.get("patch", ""),
                    additions=f["additions"],
                    deletions=f["deletions"],
                ))
            page += 1

    return files


async def _fetch_gitlab_diff(project_id, mr_iid: int) -> List[ChangedFile]:
    url = f"{GITLAB_API}/projects/{project_id}/merge_requests/{mr_iid}/changes"
    headers = {"PRIVATE-TOKEN": settings.GITLAB_TOKEN}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    files = []
    for change in data.get("changes", []):
        path = change["new_path"]
        if _should_skip(path):
            continue

        status = "removed" if change.get("deleted_file") else (
            "added" if change.get("new_file") else "modified"
        )
        files.append(ChangedFile(
            path=path,
            status=status,
            patch=change.get("diff", ""),
            additions=change.get("diff", "").count("\n+"),
            deletions=change.get("diff", "").count("\n-"),
        ))

    return files


def _should_skip(path: str) -> bool:
    if any(path.endswith(ext) for ext in settings.IGNORED_EXTENSIONS):
        return True
    if any(path.startswith(p) or f"/{p}" in path for p in settings.IGNORED_PATHS):
        return True
    return False