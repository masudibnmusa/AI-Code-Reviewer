# ============================================================
# app/review_engine/style_checker.py — LLM: naming, readability
# ============================================================
from typing import List

from app.diff_processing.diff_fetcher import ChangedFile
from app.review_engine.prompt_templates import STYLE_CHECK_PROMPT
from app.review_engine.llm import call_llm, parse_json_findings
from app.static_analysis.linter_runner import Finding


async def check_style(file: ChangedFile, context: str) -> List[Finding]:
    if file.status == "removed" or not file.patch:
        return []

    prompt = STYLE_CHECK_PROMPT.format(file_path=file.path, patch=file.patch)
    raw = await call_llm(prompt)
    issues = parse_json_findings(raw)

    return [
        Finding(
            file_path=file.path,
            line=issue.get("line", 1),
            message=issue.get("message", ""),
            severity="info",
            source="llm-style",
        )
        for issue in issues
    ]