import os
from dataclasses import dataclass
from typing import Optional, Tuple

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


@dataclass(frozen=True)
class Settings:
    app_name: str = "DevLaunch-AI"
    app_environment: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    github_token: Optional[str] = os.getenv("GITHUB_TOKEN")
    vercel_token: Optional[str] = os.getenv("VERCEL_TOKEN")
    vercel_team_id: Optional[str] = os.getenv("VERCEL_TEAM_ID")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: Tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()
    )
    storage_dir: str = os.getenv("STORAGE_DIR", "../storage")

    @property
    def is_development(self) -> bool:
        return self.app_environment.lower() == "development"

    @property
    def GROQ_API_KEY(self) -> Optional[str]:
        return self.groq_api_key

    @property
    def GITHUB_TOKEN(self) -> Optional[str]:
        return self.github_token

    @property
    def VERCEL_TOKEN(self) -> Optional[str]:
        return self.vercel_token

    @property
    def VERCEL_TEAM_ID(self) -> Optional[str]:
        return self.vercel_team_id

    @property
    def GROQ_MODEL(self) -> str:
        return self.groq_model


settings = Settings()
