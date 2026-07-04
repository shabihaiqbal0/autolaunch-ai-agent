"""
backend/deployment/vercel_client.py

Vercel Client — triggers a deployment on Vercel from a GitHub repo,
polls until it's ready, and returns the live URL.
"""

import os
import time
import requests

try:
    from backend.config import settings
    VERCEL_TOKEN = settings.VERCEL_TOKEN
    VERCEL_TEAM_ID = getattr(settings, "VERCEL_TEAM_ID", "")
except Exception:
    VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
    VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")

VERCEL_API = "https://api.vercel.com"


class VercelClientError(Exception):
    """Raised when a Vercel operation fails."""
    pass


class VercelClient:
    def __init__(self, token: str = None):
        self.token = token or VERCEL_TOKEN
        if not self.token:
            raise VercelClientError("VERCEL_TOKEN not set in config.py or .env")
        self.team_id = VERCEL_TEAM_ID

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _params(self) -> dict:
        return {"teamId": self.team_id} if self.team_id else {}

    def deploy(self, repo_name: str, github_username: str, poll_seconds: int = 5, timeout_seconds: int = 180) -> str:
        payload = {
            "name": repo_name,
            "gitSource": {
                "type": "github",
                "repo": f"{github_username}/{repo_name}",
                "ref": "main",
            },
        }
        response = requests.post(f"{VERCEL_API}/v13/deployments", json=payload, headers=self._headers(), params=self._params())

vercel_client = None
try:
    vercel_client = VercelClient()
except VercelClientError:
    pass
