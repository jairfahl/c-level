from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "dev-secret-key"
    APP_DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mentor:mentor123@localhost:5432/mentor_cfo"
    DATABASE_URL_SYNC: str = "postgresql://mentor:mentor123@localhost:5432/mentor_cfo"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TIMEOUT: int = 30

    # JWT
    JWT_SECRET_KEY: str = "dev-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # LLM Cache
    LLM_CACHE_TTL: int = 86400

    # API Credit Budget (USD)
    API_CREDIT_BUDGET: float = 5.0
    API_CREDIT_WARNING_THRESHOLD: float = 0.50
    ANTHROPIC_INPUT_PRICE_PER_1M: float = 3.0
    ANTHROPIC_OUTPUT_PRICE_PER_1M: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
