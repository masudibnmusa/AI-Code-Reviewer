# ============================================================
# tests/test_bug_checker.py
# ============================================================
import pytest
from unittest.mock import AsyncMock, patch

from app.review_engine.bug_checker import check_bugs
from app.diff_processing.diff_fetcher import ChangedFile


@pytest.mark.asyncio
async def test_check_bugs_returns_findings():
    file = ChangedFile(
        path="app/utils.py",
        status="modified",
        patch="@@ -1,3 +1,4 @@\n+def divide(a, b):\n+    return a / b",
        additions=2,
        deletions=0,
    )

    mock_llm_response = (
        '[{"line": 2, "message": "No handling for division by zero", "confidence": "high"}]'
    )

    with patch("app.review_engine.bug_checker.call_llm", new=AsyncMock(return_value=mock_llm_response)):
        findings = await check_bugs(file, context="def divide(a, b):\n    return a / b")

    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].severity == "error"
    assert findings[0].source == "llm-bug"


@pytest.mark.asyncio
async def test_check_bugs_skips_removed_files():
    file = ChangedFile(path="old.py", status="removed", patch="", additions=0, deletions=10)
    findings = await check_bugs(file, context="")
    assert findings == []


@pytest.mark.asyncio
async def test_check_bugs_handles_empty_llm_response():
    file = ChangedFile(path="app/utils.py", status="modified", patch="@@ -1 +1 @@\n+x=1", additions=1, deletions=0)

    with patch("app.review_engine.bug_checker.call_llm", new=AsyncMock(return_value="[]")):
        findings = await check_bugs(file, context="x=1")

    assert findings == []


@pytest.mark.asyncio
async def test_check_bugs_low_confidence_maps_to_warning():
    file = ChangedFile(path="app/utils.py", status="modified", patch="@@ -1 +1 @@\n+x=1", additions=1, deletions=0)
    mock_response = '[{"line": 1, "message": "Possible issue", "confidence": "low"}]'

    with patch("app.review_engine.bug_checker.call_llm", new=AsyncMock(return_value=mock_response)):
        findings = await check_bugs(file, context="x=1")

    assert findings[0].severity == "warning"