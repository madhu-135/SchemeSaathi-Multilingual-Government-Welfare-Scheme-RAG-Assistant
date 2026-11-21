"""Application configuration settings for SchemeSaathi.

Managed via Pydantic Settings with automatic environment variable parsing
and fallback to .env files.
"""

from functools import lru_cache
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory paths - dynamically resolved
def _resolve_base_dir() -> Path:
    """Resolve repository base directory safely for both local dev and Docker container."""
    curr = Path(__file__).resolve().parent  # app/
    # Check parent.parent (repo root in local dev: backend/app -> backend -> root)
    if (curr.parent.parent / "data").exists():
        return curr.parent.parent
    # Check parent (Docker container root: /app/app -> /app)
    if (curr.parent / "data").exists():
        return curr.parent
    # Fallback to local repo root assumption
    return curr.parent.parent


BASE_DIR = _resolve_base_dir()
DEFAULT_RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DEFAULT_INDEX_DATA_DIR = BASE_DIR / "data" / "index"


class Settings(BaseSettings):
    """Central configuration class for SchemeSaathi backend."""

    # Anthropic API Configuration
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # MongoDB Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "schemesaathi"

    # Multilingual Sentence Transformer Model (E5 requires 'query: ' and 'passage: ' prefixes)
    EMBED_MODEL: str = "intfloat/multilingual-e5-small"

    # RAG Retrieval Configuration
    TOP_K: int = 4
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    SIMILARITY_THRESHOLD: float = 0.80

    # Directory Paths
    RAW_DATA_DIR: Path = DEFAULT_RAW_DATA_DIR
    INDEX_DATA_DIR: Path = DEFAULT_INDEX_DATA_DIR

    @field_validator("RAW_DATA_DIR", "INDEX_DATA_DIR", mode="after")
    @classmethod
    def resolve_paths(cls, v: Path) -> Path:
        if not v.is_absolute():
            # If already exists relative to cwd
            if v.exists():
                return v.resolve()
            # Try relative to BASE_DIR
            if (BASE_DIR / v).exists():
                return (BASE_DIR / v).resolve()
            # If specified with ../ (e.g. from backend perspective)
            clean_rel = str(v).replace("../", "").replace("..\\", "")
            if (BASE_DIR / clean_rel).exists():
                return (BASE_DIR / clean_rel).resolve()
        return v

    # Application Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        # Read from root .env or backend .env if available
        env_file=(BASE_DIR / ".env", BASE_DIR / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
