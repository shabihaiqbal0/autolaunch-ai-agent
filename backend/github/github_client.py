"""
backend/github/github_client.py

GitHub Client — creates repos and pushes local project code to GitHub.
Uses PyGithub for repo creation, plain git commands for commit/push
(more reliable than reimplementing git over the REST API).
"""

import os
import subprocess
from github import Github, GithubException

try:
    from backend.config import settings
    GITHUB_TOKEN = getattr(settings, "GITHUB_TOKEN", None) or os.getenv("GITHUB_TOKEN", "")
except Exception:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


class GitHubClientError(Exception):
    """Raised when a GitHub operation fails."""
    pass


def _run(cmd: str, cwd: str) -> str:
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitHubClientError(f"Command failed: {cmd}\n{result.stderr.strip()}")
    return result.stdout.strip()


def _has_git(project_path: str) -> bool:
    return os.path.isdir(os.path.join(project_path, ".git"))


class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or GITHUB_TOKEN
        if not self.token:
            raise GitHubClientError("GITHUB_TOKEN not set in config.py or .env")
        try:
            self.gh = Github(self.token)
            self.gh.get_user()
        except Exception as exc:
            raise GitHubClientError(f"GitHub authentication failed: {exc}") from exc

    def ensure_repo_exists(self, repo_name: str, private: bool = False) -> str:
        """Returns the repo's clone URL, creating the repo if it doesn't exist yet."""
        try:
            user = self.gh.get_user()
        except Exception as exc:
            raise GitHubClientError(f"GitHub authentication failed: {exc}") from exc

        try:
            repo = user.get_repo(repo_name)
            return repo.clone_url
        except GithubException as e:
            if e.status == 404:
                try:
                    repo = user.create_repo(repo_name, private=private, auto_init=False)
                    return repo.clone_url
                except Exception as exc:
                    raise GitHubClientError(f"GitHub repo creation failed: {exc}") from exc
            raise GitHubClientError(f"Failed to check/create repo: {e}")

    def push_project(self, project_path: str, repo_name: str, username: str, private: bool = False) -> str:
        """
        Commits and pushes the local project folder to the given repo.
        Returns the repo's public GitHub URL.
        """
        clone_url = self.ensure_repo_exists(repo_name, private)
        auth_url = clone_url.replace("https://", f"https://{self.token}@")

        if not _has_git(project_path):
            _run("git init", cwd=project_path)

        _run("git add .", cwd=project_path)

        try:
            _run('git commit -m "AutoLaunch: automated commit"', cwd=project_path)
        except GitHubClientError as e:
            if "nothing to commit" not in str(e).lower():
                raise

        _run("git branch -M main", cwd=project_path)

        try:
            _run("git remote remove origin", cwd=project_path)
        except GitHubClientError:
            pass  # no remote existed yet, that's fine

        _run(f"git remote add origin {auth_url}", cwd=project_path)
        _run("git push -u origin main --force", cwd=project_path)

        return f"https://github.com/{username}/{repo_name}"

    def get_repo_info(self, repo_name: str) -> dict:
        """Returns basic metadata about an existing repo."""
        user = self.gh.get_user()
        try:
            repo = user.get_repo(repo_name)
            return {
                "name": repo.name,
                "url": repo.html_url,
                "private": repo.private,
                "default_branch": repo.default_branch,
                "created_at": repo.created_at.isoformat(),
            }
        except GithubException as e:
            raise GitHubClientError(f"Repo not found: {e}")


# Shared instance, same pattern as the rest of the app
try:
    github_client = GitHubClient()
except Exception:
    github_client = None