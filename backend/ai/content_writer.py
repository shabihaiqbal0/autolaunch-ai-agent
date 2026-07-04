"""
backend/ai/content_writer.py

AI Content Writer — generates all written content for a project:
description, README, portfolio blurb, case study, blog post.

Uses the shared AI engine from ai_engine.py — no separate Groq setup here.
"""

from backend.ai.ai_engine import engine, AIEngineError


class ContentWriterError(Exception):
    """Raised when content generation fails."""
    pass


class ContentWriter:
    def __init__(self):
        if engine is None:
            raise ContentWriterError(
                "AI engine is not available — check GROQ_API_KEY in config.py or .env"
            )
        self.engine = engine

    def _generate(self, prompt: str) -> str:
        try:
            return self.engine.ask(prompt)
        except AIEngineError as e:
            raise ContentWriterError(f"Content generation failed: {e}")

    def project_description(self, analysis: dict) -> str:
        """Short 2-3 sentence description, used on portfolio cards, GitHub 'About', etc."""
        prompt = f"""Write a short, punchy 2-3 sentence project description
based on this analysis. No fluff, no buzzwords, written for a potential client.

PROJECT ANALYSIS:
{analysis}
"""
        return self._generate(prompt)

    def readme(self, analysis: dict, live_url: str = None) -> str:
        """Full README.md content for the GitHub repo."""
        url_line = f"\nLive demo: {live_url}\n" if live_url else ""
        prompt = f"""Write a complete, professional README.md in Markdown for this project.
Include: Title, one-line tagline, Overview, Features, Tech Stack, Setup Instructions,
Usage, and a Contact/Author section.
{url_line}
PROJECT ANALYSIS:
{analysis}
"""
        return self._generate(prompt)

    def portfolio_blurb(self, analysis: dict) -> str:
        """Client-facing description for a portfolio site (different tone than README)."""
        prompt = f"""Write a portfolio-site project entry for a freelance AI developer.
Focus on the business problem solved and the result — not code details.
Keep it to one short paragraph, client-facing tone, no technical jargon.

PROJECT ANALYSIS:
{analysis}
"""
        return self._generate(prompt)

    def case_study(self, analysis: dict) -> str:
        """Longer case study — Problem, Approach, Solution, Result."""
        prompt = f"""Write a short case study (300-400 words) for this project using
this structure: Problem, Approach, Solution, Result. Written for potential
freelance clients evaluating whether to hire this developer.

PROJECT ANALYSIS:
{analysis}
"""
        return self._generate(prompt)

    def blog_post(self, analysis: dict) -> str:
        """Longer-form blog post about building the project."""
        prompt = f"""Write a blog post (500-700 words) about building this project.
Write in first person, as the developer. Cover: why I built it, key technical
decisions, challenges faced, and what I'd improve next. Conversational but
professional tone.

PROJECT ANALYSIS:
{analysis}
"""
        return self._generate(prompt)

    def generate_all(self, analysis: dict, live_url: str = None) -> dict:
        """Convenience method — generates everything in one call."""
        return {
            "description": self.project_description(analysis),
            "readme": self.readme(analysis, live_url),
            "portfolio_blurb": self.portfolio_blurb(analysis),
            "case_study": self.case_study(analysis),
            "blog_post": self.blog_post(analysis),
        }


# Shared instance, same pattern as ai_engine.py
try:
    writer = ContentWriter()
except ContentWriterError:
    writer = None