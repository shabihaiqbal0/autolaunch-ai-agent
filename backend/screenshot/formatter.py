"""
backend/publishing/formatter.py

Formatter — takes generic project content (from content_writer.py) and
reformats it for each specific platform. Each platform gets its own
tone, length, and structure — not the same text pasted everywhere.
"""

from backend.ai.ai_engine import engine, AIEngineError


class FormatterError(Exception):
    """Raised when platform-specific formatting fails."""
    pass


class Formatter:
    def __init__(self):
        if engine is None:
            raise FormatterError("AI engine unavailable — check GROQ_API_KEY")
        self.engine = engine

    def _format(self, prompt: str) -> str:
        try:
            return self.engine.ask(prompt)
        except AIEngineError as e:
            raise FormatterError(f"Formatting failed: {e}")

    def for_linkedin(self, analysis: dict, live_url: str = None) -> str:
        url_line = f"\nLive demo: {live_url}" if live_url else ""
        prompt = f"""Write a LinkedIn post announcing this project. Professional
tone, focus on the business problem solved, 3-5 short paragraphs, end with
a soft call to action. Include 3-5 relevant hashtags at the end.{url_line}

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def for_twitter(self, analysis: dict, live_url: str = None) -> str:
        url_line = f" Live: {live_url}" if live_url else ""
        prompt = f"""Write a short, punchy X (Twitter) post (under 280 characters)
announcing this project. Casual, confident tone. Include 1-2 hashtags.{url_line}

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def for_facebook(self, analysis: dict, live_url: str = None) -> str:
        url_line = f"\nCheck it out: {live_url}" if live_url else ""
        prompt = f"""Write a friendly, conversational Facebook post about this
project, aimed at a general (non-technical) audience. 2-3 short paragraphs.{url_line}

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def for_instagram(self, analysis: dict) -> str:
        prompt = f"""Write an Instagram caption for a post showcasing this project.
Short, visual-first language (assume a screenshot/video accompanies it),
end with 5-8 relevant hashtags.

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def for_fiverr(self, analysis: dict) -> str:
        prompt = f"""Write a Fiverr gig portfolio entry for this project. Written
to attract a client browsing gigs — focus on the result delivered and the
skill demonstrated, not technical implementation. 2-3 sentences.

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def for_upwork(self, analysis: dict) -> str:
        prompt = f"""Write an Upwork portfolio project entry for this project.
Client-facing, results-first tone, slightly more detailed than a Fiverr
listing since Upwork clients read more before hiring. 1 short paragraph.

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def for_contra(self, analysis: dict) -> str:
        prompt = f"""Write a Contra portfolio project entry for this project.
Modern, confident, slightly more casual tone than Upwork — Contra attracts
younger independent clients. 1 short paragraph.

PROJECT ANALYSIS:
{analysis}
"""
        return self._format(prompt)

    def format_all(self, analysis: dict, live_url: str = None) -> dict:
        """Convenience method — formats content for every platform in one call."""
        return {
            "linkedin": self.for_linkedin(analysis, live_url),
            "twitter": self.for_twitter(analysis, live_url),
            "facebook": self.for_facebook(analysis, live_url),
            "instagram": self.for_instagram(analysis),
            "fiverr": self.for_fiverr(analysis),
            "upwork": self.for_upwork(analysis),
            "contra": self.for_contra(analysis),
        }


# Shared instance, same pattern as the rest of the app
try:
    formatter = Formatter()
except FormatterError:
    formatter = None