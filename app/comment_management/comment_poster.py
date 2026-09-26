# ============================================================
# app/comment_management/comment_poster.py — Post inline + summary
# ============================================================
import httpx
from typing import List

from app.config import settings
from app.static_analysis.linter_runner import Finding

GITHUB_API = "https://api.github.com"
GITLAB_API = "https://gitlab.com/api/v4"

SEVERITY_EMOJI = {"blocking": "🚫", "suggestion": "💡", "nitpick": "✏️"}


async def post_review(repo_or_project, pr_or_mr_number, head_sha, comments: List[Finding], provider: str):
    if provider == "github":
        return await _post_github_review(repo_or_project, pr_or_mr_number, head_sha, comments)
    elif provider == "gitlab":
        return await _post_gitlab_review(repo_or_project, pr_or_mr_number, comments)
    raise ValueError(f"Unknown provider: {provider}")


def _build_summary(comments: List[Finding]) -> str:
    if not comments:
        return "## 🤖 AI Code Review\n\nNo issues found. Looks good!"

    counts = {"blocking": 0, "suggestion": 0, "nitpick": 0}
    for c in comments:
        counts[c.severity] = counts.get(c.severity, 0) + 1

    lines = ["## 🤖 AI Code Review", ""]
    lines.append(f"Found **{len(comments)}** issue(s): "
                 f"{counts['blocking']} blocking, {counts['suggestion']} suggestion(s), "
                 f"{counts['nitpick']} nitpick(s).")
    lines.append("")

    for c in comments:
        emoji = SEVERITY_EMOJI.get(c.severity, "•")
        lines.append(f"- {emoji} `{c.file_path}:{c.line}` — {c.message} _(source: {c.source})_")

    return "\n".join(lines)


async def _post_github_review(repo_full_name, pr_number, head_sha, comments: List[Finding]):
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    posted = []

    async with httpx.AsyncClient() as client:
        if settings.ENABLE_INLINE_COMMENTS:
            for c in comments:
                url = f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}/comments"
                body = {
                    "body": f"{SEVERITY_EMOJI.get(c.severity, '')} **[{c.severity}]** {c.message} _(source: {c.source})_",
                    "commit_id": head_sha,
                    "path": c.file_path,
                    "line": c.line,
                    "side": "RIGHT",
                }
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 201:
                    posted.append(c)
        else:
            posted = comments

        summary_url = f"{GITHUB_API}/repos/{repo_full_name}/issues/{pr_number}/comments"
        await client.post(summary_url, headers=headers, json={"body": _build_summary(comments)})

    return posted


async def _post_gitlab_review(project_id, mr_iid, comments: List[Finding]):
    headers = {"PRIVATE-TOKEN": settings.GITLAB_TOKEN}
    posted = comments  # GitLab inline discussion API needs diff position metadata; summary-only for MVP

    async with httpx.AsyncClient() as client:
        url = f"{GITLAB_API}/projects/{project_id}/merge_requests/{mr_iid}/notes"
        await client.post(url, headers=headers, json={"body": _build_summary(comments)})

    return posted