# ============================================================
# app/config.py — API keys, repo settings, severity thresholds
# ============================================================
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    # Server
    PORT: int = int(os.getenv("PORT", 8000))

    # Git providers
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    GITLAB_WEBHOOK_SECRET: str = os.getenv("GITLAB_WEBHOOK_SECRET", "")

    # LLM
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", 2000))

    # Review behavior
    MAX_FILES_PER_REVIEW: int = int(os.getenv("MAX_FILES_PER_REVIEW", 50))
    CONTEXT_LINES: int = int(os.getenv("CONTEXT_LINES", 15))
    ENABLE_STATIC_ANALYSIS: bool = os.getenv("ENABLE_STATIC_ANALYSIS", "true").lower() == "true"
    ENABLE_INLINE_COMMENTS: bool = os.getenv("ENABLE_INLINE_COMMENTS", "false").lower() == "true"

    # Severity thresholds — comments below this severity are dropped
    MIN_SEVERITY: str = os.getenv("MIN_SEVERITY", "nitpick")  # blocking | suggestion | nitpick

    # File filtering
    IGNORED_EXTENSIONS: List[str] = field(
        default_factory=lambda: [".lock", ".min.js", ".map", ".svg", ".png", ".jpg"]
    )
    IGNORED_PATHS: List[str] = field(
        default_factory=lambda: ["node_modules/", "vendor/", "dist/", "build/"]
    )

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_RPM", 30))


settings = Settings()