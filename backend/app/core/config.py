import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    TELEGRAM_CHAT_ID: str = "YOUR_CHAT_ID"
    DATABASE_URL: str = str(BASE_DIR / "memecoin_tracker.db")
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

def load_yaml_config():
    yaml_path = BASE_DIR / "config.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}
