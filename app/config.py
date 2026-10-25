import os
from pathlib import Path
from pydantic import BaseModel, Field


def load_dotenv(env_path: str | Path = ".env") -> None:
    """Loads key-value pairs from a .env file into os.environ without overriding existing vars."""
    path = Path(env_path)
    if not path.is_file():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val


load_dotenv()


class Settings(BaseModel):
    # App
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Divar API (Kenar SDK & v2)
    kenar_app_slug: str = Field(default_factory=lambda: os.getenv("KENAR_APP_SLUG", os.getenv("DIVAR_APP_SLUG", "")))
    kenar_api_key: str = Field(default_factory=lambda: os.getenv("KENAR_API_KEY", os.getenv("DIVAR_API_KEY", "")))
    kenar_oauth_secret: str = Field(default_factory=lambda: os.getenv("KENAR_OAUTH_SECRET", ""))
    kenar_oauth_redirect_url: str = Field(default_factory=lambda: os.getenv("KENAR_OAUTH_REDIRECT_URL", ""))
    divar_base_url: str = Field(default_factory=lambda: os.getenv("DIVAR_BASE_URL", "https://api.divar.ir"))

    # Telegram Bot
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_bot_username: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_USERNAME", ""))

    # Database
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./test.db" if os.getenv("APP_ENV") == "test" else "postgresql+asyncpg://postgres:postgres@localhost:5432/vehicle_radar"
        )
    )


settings = Settings()
