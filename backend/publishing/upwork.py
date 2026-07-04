"""
backend/publishing/upwork.py

Upwork content generator — produces a portfolio project entry for the
user's Upwork profile. Upwork clients tend to read more before hiring
than Fiverr browsers do, so this is slightly longer and more detailed
than the Fiverr entry, while staying client-facing (not technical).
"""

from backend.ai.ai_engine import engine, AIEngineError


class UpworkError(Exception):
    """Raised when Upwork content generation fails."""
    pass


def generate(analysis: dict) -> str:
    """
    Returns an Upwork portfolio project entry for this project.
    Copy this manually into the Upwork portfolio section — no auto-posting
    API exists for portfolio items.
    """
    if engine is None:
        raise UpworkError("AI engine unavailable — check GROQ_API_KEY")

    prompt = f"""Write an Upwork portfolio project entry for this project.
Client-facing, results-first tone. Slightly more detailed than a Fiverr
listing since Upwork clients read more before hiring — one solid paragraph
covering the problem, the approach, and the outcome. No technical jargon,
no code details.

PROJECT ANALYSIS:
{analysis}
"""

    try:
        return engine.ask(prompt)
    except AIEngineError as e:
        raise UpworkError(f"Failed to generate content: {e}")