# ============================================================
# tests/test_deduplicator.py
# ============================================================
from app.comment_management.deduplicator import deduplicate_comments
from app.static_analysis.linter_runner import Finding


def test_deduplicates_similar_findings_same_line():
    findings = [
        Finding(file_path="a.py", line=10, message="Unused variable 'x'", severity="warning", source="pylint"),
        Finding(file_path="a.py", line=10, message="Variable 'x' is unused", severity="warning", source="llm-style"),
    ]

    result = deduplicate_comments(findings)
    assert len(result) == 1
    # static analysis finding should be preferred over the LLM one
    assert result[0].source == "pylint"


def test_keeps_distinct_findings():
    findings = [
        Finding(file_path="a.py", line=10, message="Unused variable 'x'", severity="warning", source="pylint"),
        Finding(file_path="a.py", line=50, message="SQL injection risk", severity="error", source="bandit"),
    ]

    result = deduplicate_comments(findings)
    assert len(result) == 2


def test_merges_findings_within_line_proximity():
    findings = [
        Finding(file_path="a.py", line=10, message="Missing docstring for function", severity="info", source="llm-style"),
        Finding(file_path="a.py", line=11, message="Function is missing a docstring", severity="info", source="pylint"),
    ]

    result = deduplicate_comments(findings)
    assert len(result) == 1


def test_handles_empty_input():
    assert deduplicate_comments([]) == []


def test_separates_findings_across_files():
    findings = [
        Finding(file_path="a.py", line=10, message="Same message here", severity="warning", source="pylint"),
        Finding(file_path="b.py", line=10, message="Same message here", severity="warning", source="pylint"),
    ]

    result = deduplicate_comments(findings)
    assert len(result) == 2