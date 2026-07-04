"""
backend/auth/__init__.py

Auth package — centralizes credential checks for all external services
(Groq, GitHub, Vercel). Other modules can call check_all_credentials()
before running a pipeline, instead of failing halfway through with an
unclear error.
"""

import os

try:
    from backend.config import settings
except Exception:
    settings = None


def _get(key: str, default: str = "") -> str:
    """Reads a setting from config.py if available, else falls back to env vars."""
    if settings is not None and hasattr(settings, key):
        return getattr(settings, key) or default
    return os.getenv(key, default)


class CredentialStatus:
    """Simple result object returned by check_all_credentials()."""
    def __init__(self):
        self.groq_ok = bool(_get("GROQ_API_KEY"))
        self.github_ok = bool(_get("GITHUB_TOKEN"))
        self.vercel_ok = bool(_get("VERCEL_TOKEN"))

    @property
    def all_ok(self) -> bool:
        return self.groq_ok and self.github_ok and self.vercel_ok

    def missing(self) -> list[str]:
        missing = []
        if not self.groq_ok:
            missing.append("GROQ_API_KEY")
        if not self.github_ok:
            missing.append("GITHUB_TOKEN")
        if not self.vercel_ok:
            missing.append("VERCEL_TOKEN")
        return missing

    def to_dict(self) -> dict:
        return {
            "groq_ok": self.groq_ok,
            "github_ok": self.github_ok,
            "vercel_ok": self.vercel_ok,
            "all_ok": self.all_ok,
            "missing": self.missing(),
        }


def check_all_credentials() -> CredentialStatus:
    """
    Call this at the start of any pipeline run. Example:

        from backend.auth import check_all_credentials
        status = check_all_credentials()
        if not status.all_ok:
            raise RuntimeError(f"Missing credentials: {status.missing()}")
    """
    return CredentialStatus()