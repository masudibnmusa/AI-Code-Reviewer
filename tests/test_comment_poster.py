# ============================================================
# tests/test_comment_poster.py
# ============================================================
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.comment_management.comment_poster import (
    post_review,
    _build_summary,
)
from app.static_analysis.linter_runner import Finding


def test_build_summary_no_issues():
    summary = _build_summary([])
    assert "No issues found" in summary


def test_build_summary_with_issues():
    findings = [
        Finding(file_path="a.py", line=5, message="Bug here", severity="blocking", source="llm-bug"),
        Finding(file_path="b.py", line=8, message="Style nit", severity="nitpick", source="llm-style"),
    ]

    summary = _build_summary(findings)
    assert "Found **2** issue(s)" in summary
    assert "a.py:5" in summary
    assert "b.py:8" in summary


@pytest.mark.asyncio
async def test_post_review_unknown_provider_raises():
    with pytest.raises(ValueError):
        await post_review("owner/repo", 1, "sha123", [], provider="bitbucket")


@pytest.mark.asyncio
async def test_post_github_review_summary_only_when_inline_disabled():
    findings = [
        Finding(file_path="a.py", line=5, message="Bug here", severity="blocking", source="llm-bug"),
    ]

    with patch("app.comment_management.comment_poster.settings") as mock_settings, \
         patch("app.comment_management.comment_poster.httpx.AsyncClient") as MockClient:

        mock_settings.ENABLE_INLINE_COMMENTS = False
        mock_settings.GITHUB_TOKEN = "fake-token"

        client_instance = MockClient.return_value.__aenter__.return_value
        client_instance.post = AsyncMock(return_value=MagicMock(status_code=201))

        posted = await post_review("owner/repo", 42, "sha123", findings, provider="github")

    assert posted == findings
    client_instance.post.assert_called_once()