"""
backend/screenshot/utils/__init__.py

Shared helper functions for the screenshot module — used by both
capture.py and formatter.py so common logic (naming, cleanup, validation)
lives in one place instead of being duplicated.
"""

import os
import re
from datetime import datetime


def safe_filename(name: str) -> str:
    """
    Converts a project name into a filesystem-safe filename.
    e.g. "My AI App!" -> "my_ai_app"
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def timestamped_dir(base_dir: str, project_name: str) -> str:
    """
    Builds a unique output directory path for one capture run:
    base_dir/project_name/YYYYMMDD_HHMMSS
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = safe_filename(project_name)
    path = os.path.join(base_dir, safe_name, timestamp)
    os.makedirs(path, exist_ok=True)
    return path


def is_valid_image(path: str) -> bool:
    """Checks that a file exists and is a non-empty image file."""
    if not os.path.isfile(path):
        return False
    if os.path.getsize(path) == 0:
        return False
    valid_extensions = (".png", ".jpg", ".jpeg", ".webp")
    return path.lower().endswith(valid_extensions)


def cleanup_old_captures(base_dir: str, project_name: str, keep_latest: int = 5) -> None:
    """
    Deletes older screenshot batches for a project, keeping only the
    most recent `keep_latest` timestamped folders. Prevents the
    screenshots folder from growing forever.
    """
    safe_name = safe_filename(project_name)
    project_path = os.path.join(base_dir, safe_name)

    if not os.path.isdir(project_path):
        return

    timestamped_folders = sorted(
        [f for f in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, f))],
        reverse=True,
    )

    for folder in timestamped_folders[keep_latest:]:
        folder_path = os.path.join(project_path, folder)
        for root, _, files in os.walk(folder_path, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            os.rmdir(root)
