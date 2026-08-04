"""
RAGTUNE - Configuration and Settings Module
Enterprise-grade platform configuration management.
"""


from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Core Application Settings
    APP_NAME: str = "RAGTUNE Enterprise Knowledge Intelligence Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "ragtune-secret-key-change-in-production-2026"
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000

    # Structured Storage / Database Settings
    DATABASE_URL: str = "sqlite:///./demo_data/enterprise_db.sqlite"
    SQL_READ_ONLY: bool = True
    SQL_ROW_LIMIT: int = 100
    SQL_EXECUTION_TIMEOUT: int = 10  # seconds

    # Vector Storage & Hybrid Retrieval
    EMBEDDING_DIM: int = 384
    TOP_K_DENSE: int = 10
    TOP_K_SPARSE: int = 10
    TOP_K_RERANK: int = 5
    RRF_K: float = 60.0

    # 9-Layer Guardrails Pipeline Thresholds
    ENFORCE_GUARDRAILS: bool = True
    MAX_INPUT_LENGTH: int = 2000
    GROUNDEDNESS_THRESHOLD: float = 0.65
    PII_MASK_CHAR: str = "*"
    DENIED_SQL_KEYWORDS: list[str] = [
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "INSERT",
        "UPDATE",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
    ]
    DENIED_PROMPT_PATTERNS: list[str] = [
        "ignore previous instructions",
        "system prompt",
        "override safety",
        "bypass security",
        "jailbreak",
        "act as DAN",
    ]

    # Caching Layer Settings
    REDIS_URL: str | None = "redis://localhost:6379/0"
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600
    SEMANTIC_CACHE_THRESHOLD: float = 0.92

    # Human-in-the-Loop (HITL) Policy Settings
    HITL_CONFIDENCE_THRESHOLD: float = 0.75
    AUTO_FLAG_MUTATIONS: bool = True

    # Security & Role-Based Access Control
    DEFAULT_TENANT_ID: str = "tenant_enterprise_default"
    DEFAULT_USER_ROLE: str = "ANALYST"
    ALLOWED_ROLES: list[str] = ["ADMIN", "ANALYST", "AUDITOR", "VIEWER"]


# Global instance
settings = Settings()
