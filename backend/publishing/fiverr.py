"""
backend/publishing/fiverr.py

Fiverr content generator — Fiverr has no public posting API, so this
produces a ready-to-paste gig portfolio entry: client-facing, focused
on the result delivered, not technical implementation.
"""

from backend.ai.ai_engine import engine, AIEngineError


class FiverrError(Exception):
    """Raised when Fiverr content generation fails."""
    pass


def generate(analysis: dict) -> str:
    """
    Returns a short Fiverr portfolio entry for this project.
    Copy this manually into your Fiverr gig portfolio — no auto-posting API exists.
    """
    if engine is None:
        raise FiverrError("AI engine unavailable — check GROQ_API_KEY")

    prompt = f"""Write a Fiverr gig portfolio entry for this project. Written
to attract a client browsing gigs — focus on the result delivered and the
skill demonstrated, not technical implementation. 2-3 sentences, confident
but not salesy.

PROJECT ANALYSIS:
{analysis}
"""

    try:
        return engine.ask(prompt)
    except AIEngineError as e:
        raise FiverrError(f"Failed to generate Fiverr content: {e}")