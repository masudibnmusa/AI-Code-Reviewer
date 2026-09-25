# AI Code Reviewer

Bot that comments on PRs with style/bug suggestions.

## Overview

This project integrates with GitHub/GitLab to automatically review pull requests. It analyzes the diff, checks for bugs, style violations, security issues, and best-practice deviations, then posts inline comments directly on the PR — like a junior reviewer that never sleeps.

**Core idea:** Webhook triggers on PR open/update → fetch diff + relevant file context → run through LLM with review-focused prompts (and optionally static analysis tools) → post structured comments back via the Git provider's API.

## How It Works

1. **Webhook trigger** — GitHub/GitLab sends event on PR open/sync
2. **Diff fetching** — pull the changed files + surrounding context (not just the diff, since context matters for good reviews)
3. **Static analysis pass** (optional but recommended) — run linters/security scanners (ESLint, Bandit, Semgrep) for deterministic checks
4. **LLM review pass** — prompt LLM per file/hunk to catch logic bugs, style issues, missing edge cases, naming issues
5. **Comment deduplication** — merge LLM findings + static analysis findings, remove redundant comments
6. **Severity tagging** — classify as blocking/suggestion/nitpick
7. **Posting** — post as inline PR comments via GitHub/GitLab API, plus a summary comment
8. **Feedback loop** — track which comments get resolved vs dismissed, to tune prompt/thresholds over time

## 📁 Project Structure

```text
ai-code-reviewer/
│
├── app/
│   ├── __init__.py
│   ├── main.py                         # Webhook server entry point (FastAPI/Flask)
│   ├── config.py                       # API keys, repo settings, severity thresholds
│   │
│   ├── webhooks/
│   │   ├── __init__.py
│   │   ├── github_webhook.py            # Handle PR open/sync events
│   │   └── gitlab_webhook.py            # Handle GitLab merge request events
│   │
│   ├── diff_processing/
│   │   ├── __init__.py
│   │   ├── diff_fetcher.py              # Pull changed files + diffs via API
│   │   ├── context_builder.py           # Fetch surrounding code for context
│   │   └── hunk_splitter.py             # Break diff into reviewable chunks
│   │
│   ├── static_analysis/
│   │   ├── __init__.py
│   │   ├── linter_runner.py             # Run ESLint/Pylint/etc.
│   │   └── security_scanner.py          # Run Bandit/Semgrep
│   │
│   ├── review_engine/
│   │   ├── __init__.py
│   │   ├── bug_checker.py               # LLM: logic errors and edge cases
│   │   ├── style_checker.py             # LLM: naming, readability, conventions
│   │   ├── security_checker.py          # LLM: obvious vulnerabilities
│   │   ├── prompt_templates.py           # Review prompt templates
│   │   └── llm.py                       # Claude/GPT API wrapper
│   │
│   ├── comment_management/
│   │   ├── __init__.py
│   │   ├── deduplicator.py              # Merge overlapping findings
│   │   ├── severity_tagger.py           # Blocking/suggestion/nitpick
│   │   └── comment_poster.py            # Post inline comments + summary
│   │
│   ├── feedback/
│   │   ├── __init__.py
│   │   └── resolution_tracker.py        # Track accepted/dismissed comments
│   │
│   └── utils/
│       ├── __init__.py
│       └── rate_limiter.py              # Avoid API rate limit issues
│
├── data/
│   ├── review_history/                  # Past reviews (JSON logs)
│   └── config_rules/                    # Custom style rules per repository
│
├── tests/
│   ├── test_diff_fetcher.py
│   ├── test_bug_checker.py
│   ├── test_deduplicator.py
│   └── test_comment_poster.py
│
├── .env                                # Environment variables
├── .env.example                        # Environment variable template
├── .gitignore
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Container configuration
├── README.md
└── run.sh                              # Application startup script

## Minimum Viable Version

- `diff_fetcher.py` — pull PR diff via GitHub API
- `bug_checker.py` — one LLM call per file with a review prompt
- `comment_poster.py` — post results as a single summary comment (skip inline placement initially)

Inline comment placement, static analysis integration, and dedup logic are the v2 upgrades that make it feel production-grade.

## Setup

```bash
git clone <repo-url>
cd ai-code-reviewer
cp .env.example .env  # fill in your API keys
pip install -r requirements.txt
./run.sh
```

## Configuration

Set the following in `.env`:

- `GITHUB_TOKEN` / `GITLAB_TOKEN` — Git provider API access
- `LLM_API_KEY` — Claude/GPT API key
- `WEBHOOK_SECRET` — for verifying incoming webhook payloads
- Severity thresholds and repo-specific settings — see `app/config.py`

## License

MIT