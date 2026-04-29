from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PRInsights API"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:Sarthak%400911@localhost:5433/pr_insights"
    
    # GitHub
    GITHUB_WEBHOOK_SECRET: str = ""
    
    # AI (for later)
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
