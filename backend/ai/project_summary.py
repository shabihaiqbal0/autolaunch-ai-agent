"""
backend/ai/project_summary.py

Project Summary Builder — combines the outputs of ai_engine.py (analysis)
and content_writer.py (written content) into one structured record.
This is the object that gets saved and shown on the dashboard/portfolio
per project, so its shape should stay stable once other modules depend on it.
"""

from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional

from backend.ai.ai_engine import engine, AIEngineError
from backend.ai.content_writer import writer, ContentWriterError


class ProjectSummaryError(Exception):
    """Raised when a project summary can't be built."""
    pass


@dataclass
class ProjectSummary:
    """The single record representing one project, end to end."""
    project_name: str
    analysis: dict
    prd: Optional[str] = None
    description: Optional[str] = None
    readme: Optional[str] = None
    portfolio_blurb: Optional[str] = None
    case_study: Optional[str] = None
    blog_post: Optional[str] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    status: str = "analyzed"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


def build_summary(
    project_name: str,
    analysis: dict,
    github_url: str = None,
    live_url: str = None,
    include_content: bool = True,
    include_prd: bool = True,
) -> ProjectSummary:
    """
    Main entry point. Call this after analyze_project() (and optionally
    after GitHub push / Vercel deploy) to build the full project record.

    include_content=False skips content_writer calls if you only need
    the analysis + PRD quickly (faster, fewer API calls).
    """
    if engine is None:
        raise ProjectSummaryError("AI engine unavailable — check GROQ_API_KEY")

    summary = ProjectSummary(
        project_name=project_name,
        analysis=analysis,
        github_url=github_url,
        live_url=live_url,
    )

    if include_prd:
        try:
            summary.prd = engine.generate_prd(analysis)
        except AIEngineError as e:
            raise ProjectSummaryError(f"PRD generation failed: {e}")

    if include_content:
        if writer is None:
            raise ProjectSummaryError("Content writer unavailable — check GROQ_API_KEY")
        try:
            content = writer.generate_all(analysis, live_url=live_url)
            summary.description = content["description"]
            summary.readme = content["readme"]
            summary.portfolio_blurb = content["portfolio_blurb"]
            summary.case_study = content["case_study"]
            summary.blog_post = content["blog_post"]
        except ContentWriterError as e:
            raise ProjectSummaryError(f"Content generation failed: {e}")

    summary.status = "complete"
    return summary