"""
backend/github/repo_reader.py

Repo Reader — scans a local project folder and extracts:
1. the full file tree
2. the contents of key files (requirements.txt, main.py, package.json, etc.)

This output feeds directly into ai_engine.analyze_project(file_tree, key_files).
Keep this file's output shape stable since ai_engine depends on it.
"""

import os
from typing import Optional

IGNORE_DIRS = {
    ".git", "venv", ".venv", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".pytest_cache",
}

KEY_FILES = {
    "requirements.txt", "package.json", "app.py", "main.py",
    "streamlit_app.py", "index.js", "index.html", "README.md",
    "Procfile", "vercel.json", "Dockerfile",
}

MAX_FILE_CHARS = 3000  # cap per file so we don't blow up the AI prompt size


class RepoReaderError(Exception):
    """Raised when a project folder can't be read."""
    pass


def read_project(project_path: str) -> dict:
    """
    Main entry point. Returns:
        {
            "file_tree": [list of relative file paths],
            "key_files": {relative_path: file_contents}
        }
    """
    if not os.path.isdir(project_path):
        raise RepoReaderError(f"Path does not exist or is not a folder: {project_path}")

    file_tree = []
    key_files = {}

    for root, dirs, files in os.walk(project_path):
        # Skip ignored directories in-place so os.walk doesn't descend into them
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, project_path)
            file_tree.append(rel_path)

            if filename in KEY_FILES:
                content = _read_file_safely(full_path)
                if content is not None:
                    key_files[rel_path] = content[:MAX_FILE_CHARS]

    return {
        "file_tree": file_tree,
        "key_files": key_files,
    }


def _read_file_safely(full_path: str) -> Optional[str]:
    """Reads a file as text, ignoring encoding errors. Returns None if unreadable."""
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None