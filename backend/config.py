import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


@dataclass(frozen=True)
class Settings:
    app_name: str = "DevLaunch-AI"
    app_environment: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()
    )
    storage_dir: str = os.getenv("STORAGE_DIR", "../storage")

    @property
    def is_development(self) -> bool:
        return self.app_environment.lower() == "development"


settings = Settings()
