import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:8000"
    PORT: int = 8000
    SECRET_KEY: str = "medripple-super-secret-key-change-in-production-32chars"
    JWT_SECRET_KEY: str = "medripple-jwt-secret-key-change-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # Database
    DATABASE_URL: Optional[str] = None
    NEON_DB_CONNECTION_STRING: Optional[str] = None

    @property
    def sqlalchemy_database_uri(self) -> str:
        uri = self.DATABASE_URL or self.NEON_DB_CONNECTION_STRING or "postgresql://postgres:postgres@localhost:5432/medripple"
        # Convert postgresql:// to postgresql+psycopg:// if needed or ensure proper format for SQLAlchemy 2.x
        if uri.startswith("postgresql://") and not uri.startswith("postgresql+psycopg://"):
            uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)
        return uri

    # Groq AI
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # LangSmith
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "MedRipple"
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@medripple.com"

    # Google Calendar
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/calendar/callback"

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "medripple-storage"
    AWS_S3_PRESIGNED_URL_EXPIRY: int = 3600

settings = Settings()
