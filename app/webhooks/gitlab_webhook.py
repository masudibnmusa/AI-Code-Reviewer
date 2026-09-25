# ============================================================
# app/webhooks/gitlab_webhook.py — Handle GitLab MR events
# ============================================================
import logging

from app.diff_processing.diff_fetcher import fetch_pr_diff
from app.diff_processing.context_builder import build_context
from app.static_analysis.linter_runner import run_linters
from app.static_analysis.security_scanner import run_security_scan
from app.review_engine.bug_checker import check_bugs
from app.review_engine.style_checker import check_style
from app.review_engine.security_checker import check_security
from app.comment_management.deduplicator import deduplicate_comments
from app.comment_management.severity_tagger import tag_severity
from app.comment_management.comment_poster import post_review
from app.config import settings

logger = logging.getLogger(__name__)

RELEVANT_ACTIONS = {"open", "update", "reopen"}


async def handle_gitlab_event(payload: dict):
    if payload.get("object_kind") != "merge_request":
        return {"skipped": True, "reason": "not a merge_request event"}

    attrs = payload["object_attributes"]
    action = attrs.get("action")
    if action not in RELEVANT_ACTIONS:
        return {"skipped": True, "reason": f"unhandled action: {action}"}

    project_id = payload["project"]["id"]
    mr_iid = attrs["iid"]
    head_sha = attrs["last_commit"]["id"]

    logger.info(f"Reviewing MR !{mr_iid} on project {project_id} @ {head_sha}")

    files = await fetch_pr_diff(project_id, mr_iid, provider="gitlab")
    files = files[: settings.MAX_FILES_PER_REVIEW]

    all_comments = []

    for file in files:
        context = await build_context(project_id, file, provider="gitlab")

        static_findings = []
        if settings.ENABLE_STATIC_ANALYSIS:
            static_findings += run_linters(file, context)
            static_findings += run_security_scan(file, context)

        llm_findings = []
        llm_findings += await check_bugs(file, context)
        llm_findings += await check_style(file, context)
        llm_findings += await check_security(file, context)

        combined = deduplicate_comments(static_findings + llm_findings)
        tagged = tag_severity(combined)
        all_comments.extend(tagged)

    posted = await post_review(
        project_id, mr_iid, head_sha, all_comments, provider="gitlab"
    )

    return {"mr": mr_iid, "comments_posted": len(posted)}