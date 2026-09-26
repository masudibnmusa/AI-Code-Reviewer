# ============================================================
# app/feedback/resolution_tracker.py — Track accepted/dismissed
# ============================================================
import json
import os
from datetime import datetime, timezone
from typing import List

from app.static_analysis.linter_runner import Finding

HISTORY_DIR = "data/review_history"


def record_review(repo: str, pr_number: int, comments: List[Finding]):
    os.makedirs(HISTORY_DIR, exist_ok=True)
    record = {
        "repo": repo,
        "pr_number": pr_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "comments": [
            {
                "file_path": c.file_path,
                "line": c.line,
                "message": c.message,
                "severity": c.severity,
                "source": c.source,
                "status": "pending",  # updated later to resolved | dismissed
            }
            for c in comments
        ],
    }

    path = os.path.join(HISTORY_DIR, f"{repo.replace('/', '_')}_{pr_number}.json")
    with open(path, "w") as f:
        json.dump(record, f, indent=2)

    return path


def update_resolution(repo: str, pr_number: int, file_path: str, line: int, status: str):
    path = os.path.join(HISTORY_DIR, f"{repo.replace('/', '_')}_{pr_number}.json")
    if not os.path.exists(path):
        return False

    with open(path) as f:
        record = json.load(f)

    updated = False
    for c in record["comments"]:
        if c["file_path"] == file_path and c["line"] == line:
            c["status"] = status
            updated = True

    if updated:
        with open(path, "w") as f:
            json.dump(record, f, indent=2)

    return updated


def get_resolution_stats(repo: str = None) -> dict:
    stats = {"resolved": 0, "dismissed": 0, "pending": 0}
    if not os.path.isdir(HISTORY_DIR):
        return stats

    for fname in os.listdir(HISTORY_DIR):
        if repo and not fname.startswith(repo.replace("/", "_")):
            continue
        with open(os.path.join(HISTORY_DIR, fname)) as f:
            record = json.load(f)
        for c in record["comments"]:
            stats[c["status"]] = stats.get(c["status"], 0) + 1

    return stats