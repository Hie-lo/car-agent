import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # App
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Divar API (Kenar v2)
    divar_api_key: str = Field(default_factory=lambda: os.getenv("DIVAR_API_KEY", ""))
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
