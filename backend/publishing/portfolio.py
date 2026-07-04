"""
backend/publishing/portfolio.py

Portfolio content generator — produces a structured entry for the
user's own portfolio site (e.g. shabiha-ai-folio.lovable.app). Unlike
the freelance platforms, this returns structured fields (title, summary,
tags, etc.) since a portfolio site typically needs separate pieces to
slot into its layout, not one block of text.
"""

import json
from backend.ai.ai_engine import engine, AIEngineError


class PortfolioError(Exception):
    """Raised when portfolio content generation fails."""
    pass


def generate(analysis: dict, live_url: str = None, github_url: str = None) -> dict:
    """
    Returns a structured portfolio entry:
        {
            "title": str,
            "tagline": str,
            "summary": str,
            "tech_tags": [str, ...],
            "live_url": str | None,
            "github_url": str | None,
        }
    """
    if engine is None:
        raise PortfolioError("AI engine unavailable — check GROQ_API_KEY")

    prompt = f"""Based on this project analysis, generate a portfolio site
entry. Respond in strict JSON with these fields:
- "title": short project name (3-6 words)
- "tagline": one-line hook (under 12 words)
- "summary": one paragraph, client-facing, focused on the problem solved
  and result — no technical jargon
- "tech_tags": list of 3-6 short tech/skill tags for filtering (e.g. "Python",
  "AI Agents", "FastAPI")

PROJECT ANALYSIS:
{analysis}
"""

    try:
        raw = engine.ask(prompt, json_mode=True)
        data = json.loads(raw)
    except AIEngineError as e:
        raise PortfolioError(f"Failed to generate portfolio content: {e}")
    except json.JSONDecodeError:
        raise PortfolioError(f"AI returned invalid JSON: {raw}")

    data["live_url"] = live_url
    data["github_url"] = github_url

    return data