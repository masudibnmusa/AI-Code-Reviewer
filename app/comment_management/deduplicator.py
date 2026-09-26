# ============================================================
# app/comment_management/deduplicator.py — Merge overlapping findings
# ============================================================
from difflib import SequenceMatcher
from typing import List

from app.static_analysis.linter_runner import Finding

SIMILARITY_THRESHOLD = 0.75
LINE_PROXIMITY = 1


def deduplicate_comments(findings: List[Finding]) -> List[Finding]:
    if not findings:
        return []

    by_file = {}
    for f in findings:
        by_file.setdefault(f.file_path, []).append(f)

    deduped: List[Finding] = []

    for file_path, file_findings in by_file.items():
        file_findings.sort(key=lambda f: f.line)
        kept: List[Finding] = []

        for finding in file_findings:
            is_duplicate = False
            for existing in kept:
                if abs(existing.line - finding.line) <= LINE_PROXIMITY:
                    similarity = SequenceMatcher(
                        None, existing.message.lower(), finding.message.lower()
                    ).ratio()
                    if similarity >= SIMILARITY_THRESHOLD:
                        is_duplicate = True
                        # Prefer static analysis findings over LLM ones
                        if existing.source.startswith("llm") and not finding.source.startswith("llm"):
                            kept[kept.index(existing)] = finding
                        break
            if not is_duplicate:
                kept.append(finding)

        deduped.extend(kept)

    return deduped