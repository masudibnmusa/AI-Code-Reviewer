# ============================================================
# app/review_engine/prompt_templates.py — Review prompt templates
# ============================================================

BUG_CHECK_PROMPT = """You are reviewing a pull request diff for logic bugs and edge cases.

File: {file_path}

Full file context:

# {context}


# Diff (changes to review):
# ```diff
# {patch}
# ```

# Identify only genuine logic bugs, missing edge cases, off-by-one errors, \
# unhandled exceptions, or incorrect assumptions introduced by this diff. \
# Do NOT comment on style or naming.

# Respond ONLY as a JSON array of objects with this shape, and nothing else:
# [{{"line": <int>, "message": "<short description>", "confidence": "high"|"medium"|"low"}}]

# If there are no issues, respond with [].
# """

# STYLE_CHECK_PROMPT = """You are reviewing a pull request diff for style and readability.

# File: {file_path}

# Diff (changes to review):
# ```diff
# {patch}
# ```

# Identify naming issues, readability problems, and convention deviations \
# introduced by this diff. Do NOT comment on logic bugs or security.

# Respond ONLY as a JSON array of objects with this shape, and nothing else:
# [{{"line": <int>, "message": "<short description>", "confidence": "high"|"medium"|"low"}}]

# If there are no issues, respond with [].
# """

# SECURITY_CHECK_PROMPT = """You are reviewing a pull request diff for obvious security vulnerabilities.

# File: {file_path}

# Full file context:

# {context}


# Diff (changes to review):
# ```diff
# {patch}
# ```

# Look for injection risks, hardcoded secrets, unsafe deserialization, \
# missing input validation, and similar issues introduced by this diff.

# Respond ONLY as a JSON array of objects with this shape, and nothing else:
# [{{"line": <int>, "message": "<short description>", "confidence": "high"|"medium"|"low"}}]

# If there are no issues, respond with [].