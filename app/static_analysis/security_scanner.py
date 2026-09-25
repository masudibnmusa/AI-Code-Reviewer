# ============================================================
# app/static_analysis/security_scanner.py — Run Bandit/Semgrep
# ============================================================
import subprocess
import json
import tempfile
import os

from typing import List

from app.diff_processing.diff_fetcher import ChangedFile
from app.static_analysis.linter_runner import Finding

PYTHON_EXTS = {".py"}


def run_security_scan(file: ChangedFile, context: str) -> List[Finding]:
    if not context:
        return []

    ext = os.path.splitext(file.path)[1]
    findings = []

    if ext in PYTHON_EXTS:
        findings += _run_bandit(file.path, context)

    findings += _run_semgrep(file.path, context)
    return findings


def _run_bandit(original_path: str, context: str) -> List[Finding]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(context)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["bandit", "-f", "json", tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []
    finally:
        os.unlink(tmp_path)

    findings = []
    for issue in data.get("results", []):
        findings.append(Finding(
            file_path=original_path,
            line=issue.get("line_number", 1),
            message=issue.get("issue_text", ""),
            severity="error" if issue.get("issue_severity") == "HIGH" else "warning",
            source="bandit",
            rule_id=issue.get("test_id", ""),
        ))
    return findings


def _run_semgrep(original_path: str, context: str) -> List[Finding]:
    suffix = os.path.splitext(original_path)[1] or ".txt"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
        tmp.write(context)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["semgrep", "--config=auto", "--json", tmp_path],
            capture_output=True, text=True, timeout=60,
        )
        data = json.loads(result.stdout or "{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []
    finally:
        os.unlink(tmp_path)

    findings = []
    for result_item in data.get("results", []):
        findings.append(Finding(
            file_path=original_path,
            line=result_item.get("start", {}).get("line", 1),
            message=result_item.get("extra", {}).get("message", ""),
            severity="error",
            source="semgrep",
            rule_id=result_item.get("check_id", ""),
        ))
    return findings