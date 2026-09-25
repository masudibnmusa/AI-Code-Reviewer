# ============================================================
# app/static_analysis/linter_runner.py — Run ESLint/Pylint/etc.
# ============================================================
import subprocess
import json
import tempfile
import os
from dataclasses import dataclass
from typing import List

from app.diff_processing.diff_fetcher import ChangedFile


@dataclass
class Finding:
    file_path: str
    line: int
    message: str
    severity: str        # error | warning | info
    source: str            # "eslint" | "pylint" | "bandit" | "semgrep" | "llm"
    rule_id: str = ""


LINTERS_BY_EXT = {
    ".py": "pylint",
    ".js": "eslint",
    ".jsx": "eslint",
    ".ts": "eslint",
    ".tsx": "eslint",
}


def run_linters(file: ChangedFile, context: str) -> List[Finding]:
    ext = os.path.splitext(file.path)[1]
    linter = LINTERS_BY_EXT.get(ext)
    if not linter or not context:
        return []

    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as tmp:
        tmp.write(context)
        tmp_path = tmp.name

    try:
        if linter == "pylint":
            return _run_pylint(tmp_path, file.path)
        elif linter == "eslint":
            return _run_eslint(tmp_path, file.path)
        return []
    finally:
        os.unlink(tmp_path)


def _run_pylint(tmp_path: str, original_path: str) -> List[Finding]:
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        issues = json.loads(result.stdout or "[]")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []

    findings = []
    for issue in issues:
        findings.append(Finding(
            file_path=original_path,
            line=issue.get("line", 1),
            message=issue.get("message", ""),
            severity="warning" if issue.get("type") in ("convention", "refactor") else "error",
            source="pylint",
            rule_id=issue.get("symbol", ""),
        ))
    return findings


def _run_eslint(tmp_path: str, original_path: str) -> List[Finding]:
    try:
        result = subprocess.run(
            ["eslint", "--format=json", tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        reports = json.loads(result.stdout or "[]")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []

    findings = []
    for report in reports:
        for msg in report.get("messages", []):
            findings.append(Finding(
                file_path=original_path,
                line=msg.get("line", 1),
                message=msg.get("message", ""),
                severity="error" if msg.get("severity") == 2 else "warning",
                source="eslint",
                rule_id=msg.get("ruleId", "") or "",
            ))
    return findings