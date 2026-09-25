# ============================================================
# app/webhooks/github_webhook.py — Handle PR open/sync events
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

RELEVANT_ACTIONS = {"opened", "synchronize", "reopened"}


async def handle_github_event(event_type: str, payload: dict):
    if event_type != "pull_request":
        return {"skipped": True, "reason": f"unhandled event type: {event_type}"}

    action = payload.get("action")
    if action not in RELEVANT_ACTIONS:
        return {"skipped": True, "reason": f"unhandled action: {action}"}

    repo_full_name = payload["repository"]["full_name"]
    pr_number = payload["pull_request"]["number"]
    head_sha = payload["pull_request"]["head"]["sha"]

    logger.info(f"Reviewing PR #{pr_number} on {repo_full_name} @ {head_sha}")

    files = await fetch_pr_diff(repo_full_name, pr_number, provider="github")
    files = files[: settings.MAX_FILES_PER_REVIEW]

    all_comments = []

    for file in files:
        context = await build_context(repo_full_name, file, provider="github")

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
        repo_full_name, pr_number, head_sha, all_comments, provider="github"
    )

    return {"pr": pr_number, "comments_posted": len(posted)}