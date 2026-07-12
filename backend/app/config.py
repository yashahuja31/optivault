from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app config. All values overridable via environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    environment: str = "local"  # local | staging | production
    database_url: str = "postgresql://optivault:optivault@localhost:5432/optivault"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    # AWS (only used for demo/local scanning against a real bucket;
    # in production, per-customer credentials come from Cloud_Account rows)
    aws_default_region: str = "us-east-1"


settings = Settings()
