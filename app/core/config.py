"""
Central configuration.

Environment-driven settings for cloud + local LLM providers, semantic cache
thresholds, and database URLs. All values fall back to safe dev defaults.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """App configuration container (reads from environment)."""

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./contech.db")
    ASYNC_DATABASE_URL: str = os.getenv("ASYNC_DATABASE_URL", "")

    # --- Cloud LLM ---
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

    # --- Local OpenAI-compatible engines ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    LMSTUDIO_BASE_URL: str = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    LOCAL_LLM_ENABLED: bool = os.getenv("LOCAL_LLM_ENABLED", "true").lower() in ("1", "true", "yes")

    # --- Semantic cache ---
    SEMANTIC_CACHE_THRESHOLD: float = float(os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.92"))

    # --- Security ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey_for_dev_only")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # --- Redis ---
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- SAIBOR (commercial) ---
    SAIBOR_RATE: float = float(os.getenv("SAIBOR_RATE", "5.5"))


settings = Settings()
