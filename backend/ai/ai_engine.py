"""
backend/ai/ai_engine.py

Core AI Engine — the single place all Groq calls go through.
Other modules (content_writer.py, project_summary.py, github/analyzer.py)
should import AIEngine from here instead of creating their own Groq client.
This keeps the API key, model choice, and error handling in one place.
"""

import os
import json
from typing import Optional, List, Dict
from groq import Groq

# Try to pull settings from your existing config.py first.
# Falls back to plain environment variables if that's not set up yet,
# so this file works standalone either way.
try:
    from backend.config import settings
    GROQ_API_KEY = settings.GROQ_API_KEY
    GROQ_MODEL = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class AIEngineError(Exception):
    """Raised when the AI engine can't complete a request."""
    pass


class AIEngine:
    """
    Wraps all Groq calls. One instance can be reused across the app.

    Usage:
        engine = AIEngine()
        result = engine.analyze_project(file_tree=[...], key_files={...})
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL

        if not self.api_key:
            raise AIEngineError(
                "GROQ_API_KEY is missing. Set it in backend/config.py or .env"
            )

        self.client = Groq(api_key=self.api_key)

    def _chat(self, prompt: str, temperature: float = 0.3, json_mode: bool = False) -> str:
        """Low-level call — every other method in this class goes through this."""
        try:
            kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            raise AIEngineError(f"Groq request failed: {e}")

    def analyze_project(self, file_tree: List[str], key_files: Dict[str, str]) -> dict:
        """
        Takes a project's file tree + contents of key files (from
        github/repo_reader.py) and returns a structured analysis.
        """
        key_files_text = "\n\n".join(
            f"--- {name} ---\n{content[:3000]}" for name, content in key_files.items()
        )

        prompt = f"""You are a senior software engineer reviewing a project.

FILE TREE:
{chr(10).join(file_tree[:200])}

KEY FILE CONTENTS:
{key_files_text}

Respond in strict JSON with these fields:
- "project_type": short label (e.g. "FastAPI backend", "Streamlit app")
- "purpose": one paragraph on what this project does
- "tech_stack": list of technologies used
- "entry_point": the main file to run
- "run_command": the command to run it locally
- "deploy_target": "vercel" | "streamlit-cloud" | "huggingface-spaces" | "other"
- "missing_pieces": list of anything needed before this can be deployed
"""

        raw = self._chat(prompt, temperature=0.2, json_mode=True)

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise AIEngineError(f"AI returned invalid JSON: {raw}")

    def generate_prd(self, analysis: dict) -> str:
        """Turns a project analysis into a full Markdown PRD."""
        prompt = f"""Based on this project analysis, write a complete Product
Requirements Document (PRD) in clean Markdown with these sections in order:
Problem Statement, Vision, Goals, Target Users, Core Features,
Technical Requirements, Workflow, Roadmap (Now/Next/Later),
Success Metrics, Risks & Mitigations.

PROJECT ANALYSIS:
{json.dumps(analysis, indent=2)}

Be specific to this project. No filler text.
"""
        return self._chat(prompt, temperature=0.4)

    def ask(self, prompt: str, json_mode: bool = False) -> str:
        """
        General-purpose entry point for other modules (content_writer.py,
        analyzer.py) to reuse this same engine without duplicating setup.
        """
        return self._chat(prompt, json_mode=json_mode)


# Optional: a shared singleton so other modules can just do
#   from backend.ai.ai_engine import engine
# instead of creating a new AIEngine() every time.
try:
    engine = AIEngine()
except AIEngineError:
    engine = None  # will raise clearly the moment something tries to use it