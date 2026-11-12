import os
from typing import Optional
from dotenv import load_dotenv

# Load variables from .env file if present
load_dotenv()

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        MONGODB_URL: str = "mongodb://localhost:27017"
        DB_NAME: str = "hybrid_rec"
        SECRET_KEY: str = "hybrid-rec-secret-key-change-in-production"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days (10080 minutes)
        DEFAULT_TOP_N: int = 10
        DEFAULT_ALPHA: float = 0.5

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
            case_sensitive=True,
        )

except ImportError:
    from pydantic import BaseModel

    class Settings(BaseModel):  # type: ignore[no-redef]
        MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        DB_NAME: str = os.getenv("DB_NAME", "hybrid_rec")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "hybrid-rec-secret-key-change-in-production")
        ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))
        DEFAULT_TOP_N: int = int(os.getenv("DEFAULT_TOP_N", "10"))
        DEFAULT_ALPHA: float = float(os.getenv("DEFAULT_ALPHA", "0.5"))


settings = Settings()
