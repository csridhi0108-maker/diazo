"""
Central configuration for the DIAZO backend.
Loads values from environment variables (or a .env file in development)
using pydantic-settings. Every other module should import `settings`
from here rather than reading os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT / Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Groq (LLM explanation phrasing only — see intelligence/llm_explain.py)
    GROQ_API_KEY: str

    # Shared secret for a development ESP32 meal scale. Keep this only in the
    # backend environment and the device firmware; never expose it to React.
    ESP32_DEVICE_API_KEY: str = ""

    @property
    def clean_groq_api_key(self) -> str:
        """Defensively strips whitespace/newlines that can sneak in
        from copy-pasting the key into .env, which otherwise breaks
        the Authorization header sent to Groq."""
        return self.GROQ_API_KEY.strip()

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS_ORIGINS is stored as a comma-separated string in .env;
        split it here so main.py can pass a clean list to CORSMiddleware."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Singleton settings instance — import this everywhere else
settings = Settings()
