# ============================================================
# app/comment_management/severity_tagger.py — blocking/suggestion/nitpick
# ============================================================
from typing import List

from app.static_analysis.linter_runner import Finding
from app.config import settings

SEVERITY_ORDER = {"nitpick": 0, "suggestion": 1, "blocking": 2}

SOURCE_SEVERITY_MAP = {
    "bandit": "blocking",
    "semgrep": "blocking",
    "llm-security": "blocking",
    "llm-bug": "suggestion",
    "eslint": "suggestion",
    "pylint": "suggestion",
    "llm-style": "nitpick",
}

FINDING_SEVERITY_OVERRIDE = {
    "error": "blocking",
    "warning": "suggestion",
    "info": "nitpick",
}


def tag_severity(findings: List[Finding]) -> List[Finding]:
    min_level = SEVERITY_ORDER.get(settings.MIN_SEVERITY, 0)
    tagged = []

    for f in findings:
        category = SOURCE_SEVERITY_MAP.get(f.source, FINDING_SEVERITY_OVERRIDE.get(f.severity, "nitpick"))
        if SEVERITY_ORDER.get(category, 0) < min_level:
            continue
        f.severity = category
        tagged.append(f)

    return tagged