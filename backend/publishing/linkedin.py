"""
backend/publishing/linkedin.py

LinkedIn content generator — produces a professional announcement post
for a completed project. LinkedIn's API requires special app review for
posting on a user's behalf, so this returns a ready-to-paste draft for
now; auto-posting can be wired in later once that access is approved.
"""

from backend.ai.ai_engine import engine, AIEngineError


class LinkedInError(Exception):
    """Raised when LinkedIn content generation fails."""
    pass


def generate(analysis: dict, live_url: str = None) -> str:
    """
    Returns a LinkedIn post announcing this project.
    Copy this manually into LinkedIn — auto-posting isn't connected yet.
    """
    if engine is None:
        raise LinkedInError("AI engine unavailable — check GROQ_API_KEY")

    url_line = f"\nLive demo: {live_url}" if live_url else ""

    prompt = f"""Write a LinkedIn post announcing this project. Professional
tone, focus on the business problem solved, 3-5 short paragraphs, end with
a soft call to action. Include 3-5 relevant hashtags at the end.{url_line}

PROJECT ANALYSIS:
{analysis}
"""

    try:
        return engine.ask(prompt)
    except AIEngineError as e:
        raise LinkedInError(f"Failed to generate LinkedIn content: {e}")