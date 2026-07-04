"""
backend/github/analyzer.py

Analyzer — orchestrates repo_reader.py + ai_engine.py to produce a full
project analysis from a local folder. This is the single function the
rest of the app (main.py, project_summary.py) should call to analyze
a project — it hides the two-step read-then-analyze process.
"""

from backend.github.repo_reader import read_project, RepoReaderError
from backend.ai.ai_engine import engine, AIEngineError


class AnalyzerError(Exception):
    """Raised when a project can't be analyzed end to end."""
    pass


def analyze(project_path: str) -> dict:
    """
    Main entry point. Reads the project folder and returns a full analysis.

    Returns:
        {
            "file_tree": [...],
            "key_files_found": [...],
            "ai_summary": {...}   # from ai_engine.analyze_project()
        }
    """
    if engine is None:
        raise AnalyzerError("AI engine unavailable — check GROQ_API_KEY in config.py or .env")

    try:
        scan = read_project(project_path)
    except RepoReaderError as e:
        raise AnalyzerError(f"Could not read project folder: {e}")

    file_tree = scan["file_tree"]
    key_files = scan["key_files"]

    if not file_tree:
        raise AnalyzerError(f"No files found in project folder: {project_path}")

    try:
        ai_summary = engine.analyze_project(file_tree=file_tree, key_files=key_files)
    except AIEngineError as e:
        raise AnalyzerError(f"AI analysis failed: {e}")

    return {
        "file_tree": file_tree,
        "key_files_found": list(key_files.keys()),
        "ai_summary": ai_summary,
    }