# ============================================================
# tests/test_diff_fetcher.py
# ============================================================
import pytest
from unittest.mock import AsyncMock, patch

from app.diff_processing.diff_fetcher import (
    fetch_pr_diff,
    _should_skip,
    ChangedFile,
)


def test_should_skip_ignored_extension():
    assert _should_skip("package-lock.json".replace("json", "lock")) is True
    assert _should_skip("vendor/bundle.min.js") is True


def test_should_skip_ignored_path():
    assert _should_skip("node_modules/react/index.js") is True
    assert _should_skip("dist/bundle.js") is True


def test_should_not_skip_normal_file():
    assert _should_skip("app/main.py") is False


@pytest.mark.asyncio
async def test_fetch_github_diff_filters_ignored_files():
    mock_response_page1 = [
        {
            "filename": "app/main.py",
            "status": "modified",
            "patch": "@@ -1,2 +1,3 @@\n+import os",
            "additions": 1,
            "deletions": 0,
        },
        {
            "filename": "dist/bundle.js",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n-old\n+new",
            "additions": 1,
            "deletions": 1,
        },
    ]

    with patch("app.diff_processing.diff_fetcher.httpx.AsyncClient") as MockClient:
        client_instance = MockClient.return_value.__aenter__.return_value
        client_instance.get = AsyncMock()

        first_resp = AsyncMock()
        first_resp.json = lambda: mock_response_page1
        first_resp.raise_for_status = lambda: None

        second_resp = AsyncMock()
        second_resp.json = lambda: []
        second_resp.raise_for_status = lambda: None

        client_instance.get.side_effect = [first_resp, second_resp]

        files = await fetch_pr_diff("owner/repo", 42, provider="github")

    assert len(files) == 1
    assert files[0].path == "app/main.py"


@pytest.mark.asyncio
async def test_fetch_pr_diff_unknown_provider_raises():
    with pytest.raises(ValueError):
        await fetch_pr_diff("owner/repo", 1, provider="bitbucket")


def test_changed_file_dataclass_fields():
    f = ChangedFile(path="a.py", status="added", patch="", additions=5, deletions=0)
    assert f.path == "a.py"
    assert f.status == "added"
    assert f.additions == 5