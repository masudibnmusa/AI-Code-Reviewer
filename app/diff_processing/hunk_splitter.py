# ============================================================
# app/diff_processing/hunk_splitter.py — Break diff into chunks
# ============================================================
import re
from dataclasses import dataclass
from typing import List

from app.diff_processing.diff_fetcher import ChangedFile


@dataclass
class Hunk:
    file_path: str
    start_line: int      # starting line number in the new file
    end_line: int
    content: str          # the hunk text (with +/- markers)


HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def split_into_hunks(file: ChangedFile) -> List[Hunk]:
    if not file.patch:
        return []

    hunks = []
    lines = file.patch.split("\n")
    current_lines: List[str] = []
    start_line = None
    hunk_len = 0

    def flush():
        nonlocal current_lines, start_line, hunk_len
        if start_line is not None and current_lines:
            hunks.append(Hunk(
                file_path=file.path,
                start_line=start_line,
                end_line=start_line + max(hunk_len - 1, 0),
                content="\n".join(current_lines),
            ))
        current_lines = []
        start_line = None
        hunk_len = 0

    for line in lines:
        match = HUNK_HEADER_RE.match(line)
        if match:
            flush()
            start_line = int(match.group(1))
            hunk_len = int(match.group(2)) if match.group(2) else 1
            current_lines.append(line)
        else:
            current_lines.append(line)

    flush()
    return hunks